"""
flex_retry — Exponential-backoff wrapper for LiteLLM calls with Flex Processing.

OpenAI Flex Processing (``service_tier="flex"``) uses spare capacity, so callers
may receive a ``429 Resource Unavailable`` during peak load.  This module wraps
``litellm.acompletion`` with:

1. **Extended timeout** — 600 s (10 min) for Flex calls; 120 s otherwise.
2. **Exponential backoff** — up to ``FLEX_MAX_RETRIES`` on any ``429``/
   ``RateLimitError`` before giving up on Flex.
3. **Automatic fallback** — after exhausting Flex retries, the call is retried
   once on the *standard* tier (``service_tier`` removed) so the audit is never
   completely stalled by spare-capacity exhaustion.

Usage (lowest-level, used internally by ``BaseAgent.acompletion``)::

    from aaa.platform.flex_retry import flex_acompletion

    response = await flex_acompletion(
        model="gpt-5.5",
        service_tier="flex",
        messages=[{"role": "user", "content": "…"}],
    )
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuneable constants
# ---------------------------------------------------------------------------

FLEX_TIMEOUT_SECONDS: float = 600.0   # 10 minutes — Flex can queue before processing
DEFAULT_TIMEOUT_SECONDS: float = 120.0 # 2 minutes for standard-tier calls

FLEX_MAX_RETRIES: int = 3             # attempts on Flex before falling back
FLEX_BACKOFF_BASE: float = 2.0        # seconds; doubles each retry (2 → 4 → 8)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def flex_acompletion(**kwargs: Any) -> Any:
    """Async LiteLLM call with Flex-aware retry + standard-tier fallback.

    Parameters
    ----------
    **kwargs:
        Any keyword arguments accepted by ``litellm.acompletion``.  When
        ``service_tier="flex"`` is present the extended timeout and backoff
        logic are activated; otherwise this is a thin pass-through with the
        default timeout applied.
    """
    import litellm  # type: ignore  # optional at import time

    is_flex = kwargs.get("service_tier") == "flex"
    timeout = FLEX_TIMEOUT_SECONDS if is_flex else DEFAULT_TIMEOUT_SECONDS
    call_kwargs = {**kwargs, "timeout": timeout}

    if not is_flex:
        # Non-Flex: single attempt, no special handling.
        return await litellm.acompletion(**call_kwargs)

    # ── Flex path: exponential backoff, then standard-tier fallback ──────────
    last_exc: BaseException | None = None
    for attempt in range(1, FLEX_MAX_RETRIES + 1):
        try:
            logger.debug(
                "flex_acompletion: attempt %d/%d model=%s",
                attempt, FLEX_MAX_RETRIES, kwargs.get("model"),
            )
            return await litellm.acompletion(**call_kwargs)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_rate_limit(exc):
                # Non-retryable error (auth, bad request, …) — re-raise immediately.
                raise
            wait = FLEX_BACKOFF_BASE ** (attempt - 1)
            logger.warning(
                "flex_acompletion: 429/rate-limit on attempt %d (model=%s). "
                "Retrying in %.0f s…",
                attempt, kwargs.get("model"), wait,
            )
            await asyncio.sleep(wait)

    # ── All Flex retries exhausted → try standard tier once ─────────────────
    logger.warning(
        "flex_acompletion: Flex exhausted after %d attempts for model=%s. "
        "Falling back to standard tier.",
        FLEX_MAX_RETRIES, kwargs.get("model"),
    )
    fallback_kwargs = {**_strip_flex(kwargs), "timeout": DEFAULT_TIMEOUT_SECONDS}
    try:
        return await litellm.acompletion(**fallback_kwargs)
    except Exception as fallback_exc:
        # Surface both the original and fallback errors for debugging.
        raise RuntimeError(
            f"flex_acompletion: Flex retries exhausted ({last_exc!r}) AND "
            f"standard-tier fallback also failed: {fallback_exc!r}"
        ) from fallback_exc


__all__ = [
    "flex_acompletion",
    "FLEX_TIMEOUT_SECONDS",
    "DEFAULT_TIMEOUT_SECONDS",
    "FLEX_MAX_RETRIES",
    "FLEX_BACKOFF_BASE",
]
