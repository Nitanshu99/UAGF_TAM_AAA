"""The Flex ladder: exponential backoff on rate limits, then one standard-tier attempt.

Rate-limit pressure and tier unavailability are different failures with different
remedies, so each stays bounded by its own ceiling rather than by their product.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from aaa.platform.flex_retry.logger import (
    CLIENT_MAX_RETRIES,
    FLEX_BACKOFF_BASE,
    FLEX_MAX_RETRIES,
    _is_rate_limit,
    _strip_flex,
)

logger = logging.getLogger(__name__)


async def flex_ladder(litellm: Any, call_kwargs: dict, kwargs: dict,
                      timeout: float | None) -> Any:
    """Run the Flex attempts, then fall back to the standard tier once.

    :param litellm: The imported litellm module.
    :param call_kwargs: The Flex call's keyword arguments.
    :param kwargs: The caller's original keyword arguments, for the fallback.
    :param timeout: The resolved client ceiling.
    :returns: The provider's response.
    :raises RuntimeError: Flex was exhausted and the standard tier also failed.
    """
    # ── Flex path: exponential backoff, then standard-tier fallback ──────────
    last_exc: BaseException | None = None
    for attempt in range(1, FLEX_MAX_RETRIES + 1):
        try:
            logger.debug("flex_acompletion: attempt %d/%d model=%s",
                         attempt, FLEX_MAX_RETRIES, kwargs.get("model"))
            return await litellm.acompletion(**call_kwargs)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_rate_limit(exc):
                # Non-retryable error (auth, bad request, …) — re-raise immediately.
                raise
            wait = FLEX_BACKOFF_BASE ** (attempt - 1)
            logger.warning("flex_acompletion: 429/rate-limit on attempt %d "
                           "(model=%s). Retrying in %.0f s…",
                           attempt, kwargs.get("model"), wait)
            await asyncio.sleep(wait)

    # ── All Flex retries exhausted → try standard tier once ─────────────────
    logger.warning("flex_acompletion: Flex exhausted after %d attempts for "
                   "model=%s. Falling back to standard tier.",
                   FLEX_MAX_RETRIES, kwargs.get("model"))
    fallback_kwargs = {**_strip_flex(kwargs), "timeout": timeout,
                       "max_retries": CLIENT_MAX_RETRIES}
    try:
        return await litellm.acompletion(**fallback_kwargs)
    except Exception as fallback_exc:
        # Surface both the original and fallback errors for debugging.
        raise RuntimeError(
            f"flex_acompletion: Flex retries exhausted ({last_exc!r}) AND "
            f"standard-tier fallback also failed: {fallback_exc!r}"
        ) from fallback_exc


__all__ = ["flex_ladder"]
