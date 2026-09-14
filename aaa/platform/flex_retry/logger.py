"""Part 1 of the former ``flex_retry`` module (auto-split)."""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _timeout(name: str, default: float) -> float:
    """Read a timeout override from the environment, falling back to *default*.

    Rate-limited providers queue rather than reject: the NVIDIA NIM free tier
    (40 req/min) can hold a request well past the standard ceiling, which
    surfaces as ``litellm.Timeout`` mid-audit and silently truncates the run.
    Raising the ceiling per-deployment is cheaper than special-casing the
    provider here.

    :param name: Environment variable to read.
    :type name: str
    :param default: Value used when unset, empty or unparseable.
    :type default: float
    :returns: The effective timeout in seconds.
    :rtype: float
    """
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("%s=%r is not a number; using %.0fs.", name, raw, default)
        return default


#: 4 minutes — Flex queue + processing ceiling. Override: ``FLEX_TIMEOUT_SECONDS``.
FLEX_TIMEOUT_SECONDS: float = _timeout("FLEX_TIMEOUT_SECONDS", 240.0)


#: 2 minutes for standard-tier calls. Override: ``LLM_TIMEOUT_SECONDS``.
DEFAULT_TIMEOUT_SECONDS: float = _timeout("LLM_TIMEOUT_SECONDS", 120.0)


#: Retries the HTTP client beneath litellm may make on its own — **zero**, so the
#: ceiling passed to it bounds the whole call rather than one attempt of it.
#:
#: Fix 46 (finding R14). `openai/_base_client.py` loops
#: ``for retries_taken in range(max_retries + 1)`` and builds the request *inside*
#: that loop, so `timeout` applies per attempt; both litellm and the openai SDK
#: default `max_retries` to 2. A 300 s ceiling therefore bounded up to ~900 s of
#: wall-clock, which is how case 04 #024 recorded 319.7 s and returned `ok`, and
#: how a 347.8 s GovernanceAgent call came back under a nominal 120 s.
#:
#: Zero is the right value rather than a smaller number because this codebase now
#: has a retry policy of its own — fix 39 — which is bounded, budget-aware, and
#: written to the audit trail as `attempts`. A second, silent, triply-billed one
#: underneath it is the class of unmeasured mechanism these fixes keep removing.
CLIENT_MAX_RETRIES: int = 0


FLEX_MAX_RETRIES: int = 2             # attempts on Flex before falling back


FLEX_BACKOFF_BASE: float = 2.0        # seconds; doubles each retry (2 → 4 → 8)


def _is_rate_limit(exc: BaseException) -> bool:
    """Return True when *exc* is a 429 / RateLimitError from litellm or httpx."""
    type_name = type(exc).__name__
    if "RateLimitError" in type_name or "Timeout" in type_name:
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "resource unavailable" in msg


def _strip_flex(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *kwargs* with ``service_tier`` removed (standard tier)."""
    cleaned = dict(kwargs)
    cleaned.pop("service_tier", None)
    return cleaned
