"""Part 3 of the former ``cgsa_pull`` module (auto-split)."""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any

from aaa.tools.cgsa_pull.fetch_once import _fetch_once  # noqa: F401
from aaa.tools.cgsa_pull.logger import _BACKOFF_BASE_SECONDS, _MAX_ATTEMPTS, CGSAPullError, logger


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
            return _fetch_once(url, headers, pinned_version,
                               timeout_seconds, assessment_id, attempt)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise CGSAPullError("not_found", {"url": url}) from exc
            if exc.code == 401:
                raise CGSAPullError("unauthorised", {"url": url}) from exc
            last_exc = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_exc = exc

        sleep_for = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
        logger.warning("cgsa_pull: attempt %d/%d failed (%s); backing off %.1fs",
                       attempt, _MAX_ATTEMPTS, last_exc, sleep_for)
        time.sleep(sleep_for)

    raise CGSAPullError(
        "max_retries_exhausted",
        {"url": url, "attempts": _MAX_ATTEMPTS, "last_error": str(last_exc)},
    )
