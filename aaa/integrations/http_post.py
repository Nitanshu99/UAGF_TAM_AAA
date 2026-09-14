"""Retrying JSON POST shared by the external S6/S7 provider clients.

Mirrors the S4 ``cgsa_pull`` transport behaviour (exponential back-off,
hard-fail on auth/not-found) on top of ``httpx`` so tests can mock it
with ``respx``.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from aaa.integrations.base import ProviderError

logger = logging.getLogger(__name__)

_BACKOFF_BASE_SECONDS = 0.5


def post_json(url: str, payload: dict[str, Any], bearer_token: str | None = None,
              timeout: float = 30.0, max_attempts: int = 3) -> dict[str, Any]:
    """POST *payload* to *url* and return the parsed JSON response.

    :param url: Full endpoint URL.
    :type url: str
    :param payload: JSON-serialisable request body.
    :type payload: dict[str, Any]
    :param bearer_token: Optional bearer token for the Authorization header.
    :type bearer_token: str | None
    :param timeout: Per-request timeout in seconds.
    :type timeout: float
    :param max_attempts: Attempts before giving up on retryable errors.
    :type max_attempts: int
    :returns: Decoded JSON response body.
    :rtype: dict[str, Any]
    :raises ProviderError: On 401/404 (immediately) or exhausted retries.
    """
    headers = {"Accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=timeout)
        except httpx.HTTPError as exc:
            last_exc = exc
        else:
            if response.status_code in (401, 404):
                raise ProviderError("unauthorised" if response.status_code == 401
                                    else "not_found", {"url": url})
            if response.status_code < 400:
                return response.json()
            last_exc = httpx.HTTPStatusError(  # 5xx and other 4xx → retryable
                f"HTTP {response.status_code}", request=response.request, response=response)
        if attempt < max_attempts:
            sleep_for = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning("post_json: attempt %d/%d failed (%s); backing off %.1fs",
                           attempt, max_attempts, last_exc, sleep_for)
            time.sleep(sleep_for)
    raise ProviderError("max_retries_exhausted",
                        {"url": url, "attempts": max_attempts, "last_error": str(last_exc)})
