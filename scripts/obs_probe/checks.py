"""Sink checks for the probe: file, metrics directory, API, Loki, Langfuse."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.obs_probe.llm_call import AGENT_NAME, PROBE_MODEL
from scripts.obs_probe.remote import check_langfuse, check_loki


@dataclass
class Check:
    """Outcome of one sink check."""

    name: str
    ok: bool
    detail: str
    optional: bool = False


def check_audit_file(record: dict[str, Any]) -> Check:
    """The append-only trail must end with the probe's row."""
    path = Path("logs/audit/llm_audit.jsonl")
    try:
        last = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    except (OSError, IndexError, json.JSONDecodeError) as exc:
        return Check("llm_audit.jsonl", False, f"unreadable: {exc}")
    hit = last.get("engagement_id") == record["engagement_id"] and last.get("agent") == AGENT_NAME
    return Check("llm_audit.jsonl", hit, f"last row engagement_id={last.get('engagement_id')} "
                 f"agent={last.get('agent')} status={last.get('status')}")


def check_multiproc_dir() -> Check:
    """The shared Prometheus directory must hold this process's counter."""
    from aaa.observability.metrics.multiproc import build_registry, multiproc_dir

    path = multiproc_dir()
    if path is None:
        return Check("PROMETHEUS_MULTIPROC_DIR", False, "not set — import aaa should have set it")
    value = build_registry(path).get_sample_value(
        "aaa_llm_calls_total", {"agent": AGENT_NAME, "model": PROBE_MODEL, "status": "ok"})
    return Check("PROMETHEUS_MULTIPROC_DIR", bool(value), f"{path}: aaa_llm_calls_total{{agent="
                 f"{AGENT_NAME}}}={value}")


def check_api_metrics() -> Check:
    """The API's /metrics must expose the counter this other process wrote."""
    import httpx

    url = f"http://localhost:{os.environ.get('PLATFORM_PORT', '8000')}/metrics"
    try:
        body = httpx.get(url, timeout=5).text
    except httpx.HTTPError as exc:
        return Check("API /metrics", False, f"{url} unreachable ({exc.__class__.__name__}) — "
                     "start it with `python -m aaa api`", optional=True)
    needle = f'aaa_llm_calls_total{{agent="{AGENT_NAME}"'
    return Check("API /metrics", needle in body, f"{url} {'contains' if needle in body else 'lacks'} "
                 f"{needle}…}}")


def run_checks(probe_id: str, record: dict[str, Any]) -> list[Check]:
    """Run every sink check in order and return the outcomes."""
    return [check_audit_file(record), check_multiproc_dir(), check_api_metrics(),
            Check(*check_loki(probe_id)), Check(*check_langfuse(probe_id, record["engagement_id"]))]
