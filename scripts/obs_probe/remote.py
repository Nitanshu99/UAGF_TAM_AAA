"""Loki and Langfuse checks — both poll, because both ingest asynchronously."""
from __future__ import annotations

import os
import time
from typing import Any, Callable

import httpx

Outcome = tuple[str, bool, str, bool]


def _poll(fn: Callable[[], str | None], seconds: int) -> str | None:
    """Call *fn* until it returns a hit or *seconds* elapse."""
    deadline = time.monotonic() + seconds
    while True:
        hit = fn()
        if hit or time.monotonic() >= deadline:
            return hit
        time.sleep(2)


def check_loki(probe_id: str) -> Outcome:
    """Alloy must have shipped the audit row to Loki (queried via Grafana)."""
    grafana = os.environ.get("GRAFANA_URL", "http://localhost:3002").rstrip("/")
    auth = ("admin", os.environ.get("GF_SECURITY_ADMIN_PASSWORD", "admin"))
    url = f"{grafana}/api/datasources/proxy/uid/loki/loki/api/v1/query_range"
    query = f'{{job="aaa", agent="ObsProbe"}} |= "{probe_id}"'
    try:
        httpx.get(f"{grafana}/api/health", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        return ("Loki (via Grafana)", False,
                f"{grafana} unreachable ({exc.__class__.__name__}) — `make obs`", True)

    def attempt() -> str | None:
        now = time.time_ns()
        resp = httpx.get(url, params={"query": query, "start": now - 15 * 60 * 10**9,
                                      "end": now, "limit": 5}, auth=auth, timeout=10)
        streams: list[dict[str, Any]] = resp.json().get("data", {}).get("result", [])
        return streams[0]["values"][0][1][:120] if streams else None

    hit = _poll(attempt, 60)
    return ("Loki (via Grafana)", bool(hit), f"{query} → {hit or 'no line within 60s'}", False)


def check_langfuse(probe_id: str, engagement_id: str) -> Outcome:
    """The langfuse_otel callback must have produced a generation in the probe's session.

    Langfuse v4 runs in *events_only* mode: the legacy ``/api/public/traces``
    and ``/sessions`` endpoints answer 404; ``/api/public/v2/observations``
    is the list API and filters by ``sessionId`` — the engagement id that
    ``with_session_metadata`` attaches to every call.
    """
    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3003").rstrip("/")
    public, secret = os.environ.get("LANGFUSE_PUBLIC_KEY", ""), os.environ.get("LANGFUSE_SECRET_KEY", "")
    from aaa.observability.tracing import _is_real_key  # pylint: disable=protected-access
    if not (_is_real_key(public) and _is_real_key(secret)):
        return ("Langfuse", False, "LANGFUSE_PUBLIC_KEY/SECRET_KEY blank or placeholder — tracing off", True)

    def attempt() -> str | None:
        resp = httpx.get(f"{host}/api/public/v2/observations",
                         params={"sessionId": engagement_id, "type": "GENERATION", "limit": 5},
                         auth=(public, secret), timeout=10)
        rows = resp.json().get("data", []) if resp.status_code == 200 else []
        return f"generation {rows[0]['id']} trace={rows[0]['traceId']}" if rows else None

    hit = _poll(attempt, 90)
    return ("Langfuse", bool(hit), f"{host} session {engagement_id} → {hit or 'no generation within 90s'}"
            + ("" if hit else f" (marker {probe_id})"), False)
