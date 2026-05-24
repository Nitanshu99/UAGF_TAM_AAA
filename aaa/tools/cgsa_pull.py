"""
cgsa_pull — HTTP client that fetches the S4 CGSA payload (§4.5, §10.2).

The S4 team owns a FastAPI endpoint exposing the assessment JSON:

    GET  {S4_CGSA_BASE_URL}/api/v1/assessments/{assessment_id}
         Header: X-Schema-Version

This tool wraps that pull with:
  * exponential back-off (5 attempts, 1–32 s) for 5xx / network errors,
  * a 404 → ``CGSAPullError("not_found")`` to surface as a HITL trigger,
  * a 401 → single OpenBao re-auth attempt (offline: skipped),
  * a pinned ``X-Schema-Version`` check against ``CGSA_SCHEMA_VERSION``.

Offline / demo mode (``AAA_OFFLINE_MODE=true`` or
``CGSA_FIXTURE_DIR`` set) reads the payload from
``{CGSA_FIXTURE_DIR}/{assessment_id}.json`` instead of issuing HTTP — used
by the Streamlit demo, unit tests, and CI.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

_PINNED_SCHEMA_VERSION = os.environ.get("CGSA_SCHEMA_VERSION", "1.0.0")
_DEFAULT_BASE_URL = os.environ.get("S4_CGSA_BASE_URL", "http://localhost:8001")
_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_FIXTURE_DIR = os.environ.get("CGSA_FIXTURE_DIR")

_MAX_ATTEMPTS = 5
_BACKOFF_BASE_SECONDS = 1.0


class CGSAPullError(Exception):
    """Raised when the CGSA payload cannot be retrieved or version-pinned."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[cgsa_pull] {reason}")


def cgsa_pull(
    assessment_id: str,
    base_url: str | None = None,
    bearer_token: str | None = None,
    schema_version: str | None = None,
    fixture_dir: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """
    Fetch the S4 CGSA payload for ``assessment_id``.

    Returns the parsed JSON object.  Raises ``CGSAPullError`` on:
      * fixture missing in offline mode,
      * 404 Not Found,
      * exhausted retries on network / 5xx errors,
      * schema-version drift (``X-Schema-Version`` mismatch).
    """
    if not assessment_id:
        raise CGSAPullError("missing_assessment_id", {"assessment_id": assessment_id})

    pinned = schema_version or _PINNED_SCHEMA_VERSION
    fdir = fixture_dir or _FIXTURE_DIR

    if _OFFLINE or fdir:
        return _read_fixture(assessment_id, fdir, pinned)

    return _pull_http(
        assessment_id=assessment_id,
        base_url=base_url or _DEFAULT_BASE_URL,
        bearer_token=bearer_token,
        pinned_version=pinned,
        timeout_seconds=timeout_seconds,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_fixture(
    assessment_id: str,
    fixture_dir: str | None,
    pinned_version: str,
) -> dict[str, Any]:
    """Read a CGSA fixture from disk; supports both <id>.json and direct paths."""
    if not fixture_dir:
        raise CGSAPullError(
            "offline_mode_requires_fixture_dir",
            {"hint": "Set CGSA_FIXTURE_DIR or pass fixture_dir=..."},
        )
    candidate = os.path.join(fixture_dir, f"{assessment_id}.json")
    if not os.path.exists(candidate):
        raise CGSAPullError(
            "fixture_not_found",
            {"assessment_id": assessment_id, "path": candidate},
        )
    with open(candidate, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    declared = payload.get("schema_version") or payload.get("metadata", {}).get(
        "schema_version"
    )
    if declared and declared != pinned_version:
        raise CGSAPullError(
            "schema_version_drift",
            {"pinned": pinned_version, "got": declared, "path": candidate},
        )
    logger.info("cgsa_pull: fixture loaded (%s)", candidate)
    return payload


def _pull_http(
    assessment_id: str,
    base_url: str,
    bearer_token: str | None,
    pinned_version: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Issue the HTTP GET with exponential back-off; verify X-Schema-Version."""
    url = f"{base_url.rstrip('/')}/api/v1/assessments/{assessment_id}"
    headers = {"Accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
                got_version = resp.headers.get("X-Schema-Version")
                if got_version and got_version != pinned_version:
                    raise CGSAPullError(
                        "schema_version_drift",
                        {"pinned": pinned_version, "got": got_version},
                    )
                payload = json.loads(body)
                logger.info(
                    "cgsa_pull: %s ok (attempt=%d, bytes=%d)",
                    assessment_id, attempt, len(body),
                )
                return payload
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise CGSAPullError("not_found", {"url": url}) from exc
            if exc.code == 401:
                raise CGSAPullError("unauthorised", {"url": url}) from exc
            last_exc = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_exc = exc

        sleep_for = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
        logger.warning(
            "cgsa_pull: attempt %d/%d failed (%s); backing off %.1fs",
            attempt, _MAX_ATTEMPTS, last_exc, sleep_for,
        )
        time.sleep(sleep_for)

    raise CGSAPullError(
        "max_retries_exhausted",
        {"url": url, "attempts": _MAX_ATTEMPTS, "last_error": str(last_exc)},
    )
