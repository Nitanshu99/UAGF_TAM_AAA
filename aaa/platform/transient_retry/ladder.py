"""The backed-off retry loop one model gets — shared by a call's primary model and its fallback."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from aaa.platform.phase_budget.observed import observe_failure
from aaa.platform.transient_retry.attempts import note_retry
from aaa.platform.transient_retry.backoff import (
    MAX_RATE_LIMIT_RETRIES,
    MAX_TRANSIENT_RETRIES,
    backoff_seconds,
)
from aaa.platform.transient_retry.budget import _STOP_NOTE, HAND_OVER, _stop_reason, capped, hit_cap
from aaa.platform.transient_retry.classify import is_transient, is_upstream_rate_limit
from aaa.platform.transient_retry.latency import record_success

logger = logging.getLogger(__name__)

async def ladder(call: Callable[..., Awaitable[Any]], kwargs: dict[str, Any],
                 fallback: tuple[bool, float | None] = (False, None),
                 ) -> tuple[Any, BaseException | None, float, str]:
    """Attempt *call* with backed-off retries: ``(value, failure, last_elapsed, stopped)``.

    :param fallback: ``(has_fallback, measured_cost)``. A retry is made only while the
        fallback's attempt still fits after it; when only that attempt fits it is handed
        over (case 04, 2026-09-13: slow overload errors spent the budget and the fallback
        never ran). See :func:`.budget._stop_reason` for how the attempt is priced.
    :returns: ``stopped`` is ``""``, :data:`BUDGET_SPENT` or :data:`HAND_OVER`.
    """
    price = fallback[1]  # the fallback's attempt price, once one is known
    for attempt in range(max(MAX_TRANSIENT_RETRIES, MAX_RATE_LIMIT_RETRIES) + 1):
        started = time.monotonic()
        attempt_kwargs = capped(kwargs, price if fallback[0] else None)
        try:
            value = await call(**attempt_kwargs)
            record_success(str(kwargs.get("model", "")), time.monotonic() - started)
            return value, None, 0.0, ""
        except Exception as exc:  # noqa: BLE001 — returned to the caller, which raises it
            elapsed = time.monotonic() - started
            stopped = HAND_OVER if hit_cap(attempt_kwargs, exc, fallback[0]) else ""
            limited = is_upstream_rate_limit(exc)
            retries = MAX_RATE_LIMIT_RETRIES if limited else MAX_TRANSIENT_RETRIES
            if not stopped and (attempt >= retries or not is_transient(exc)):
                return None, exc, elapsed, ""
            observe_failure(elapsed)  # what a failing provider costs a phase (T-102)
            wait = backoff_seconds(attempt, rate_limited=limited)
            price = fallback[1] if fallback[1] is not None else elapsed
            stopped = stopped or _stop_reason(elapsed, wait, *fallback)
            if stopped:
                logger.warning("transient_retry: %s after %.1f s on model=%s; %s.", type(exc).__name__,
                               elapsed, kwargs.get("model"), _STOP_NOTE[stopped])
                return None, exc, elapsed, stopped
            note_retry(exc)
            logger.warning(
                "transient_retry: %s after %.1f s on model=%s. Retry %d of %d in %.1f s.",
                type(exc).__name__, elapsed, kwargs.get("model"), attempt + 1, retries, wait)
            await asyncio.sleep(wait)
    raise AssertionError("unreachable: the loop returns")  # pragma: no cover


__all__ = ["ladder"]
