"""Bounded retries around a provider call — fix 39 (findings R7, R13), widened 2026-09-13.

**The budget rule, and why it is this one.** A retry that cannot finish is not
free: it holds the provider, it is billed (finding R5), and the phase it belongs
to has already given up on it. So a retry is attempted only when there is room
for it. The room needed is measured, not guessed — *the failed attempt's own
elapsed time*. It is the one honest estimate available at the moment of failure:
this provider, this model, this payload, seconds ago. Against the 2026-09-03 run
that rule declines three of the five transient failures, and declines each of
them correctly — ``ScopeAgent`` had already overrun its 120 s phase budget by
62 s, ``ReportArchitect`` had 8.6 s of 180 s left, and ``ModelValidator`` had
71.4 s left against a 108.6 s attempt in a phase whose median successful call
took 158.9 s. Those three are lost to the budget being too small (finding R1),
not to the absence of a retry, and fix 34 is what recovers them.

An **unbound** deadline means no budget to respect, not a zero one: the
Verifier runs outside the phase timeout and the Orchestrator's decide loop
outside any phase at all, and both are retried unconditionally — following the
same reading of an absent binding that :mod:`aaa.platform.phase_budget` states.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aaa.platform.transient_retry.attempts import note_fallback, note_retry
from aaa.platform.transient_retry.backoff import (  # noqa: F401 — re-exported
    MAX_TRANSIENT_RETRIES,
    TRANSIENT_BACKOFF_CAP_SECONDS,
    TRANSIENT_BACKOFF_SECONDS,
    backoff_seconds,
)
from aaa.platform.transient_retry.budget import BUDGET_SPENT, HAND_OVER, fits_in_budget
from aaa.platform.transient_retry.classify import is_transient
from aaa.platform.transient_retry.fallback import fallback_model_for
from aaa.platform.transient_retry.ladder import ladder
from aaa.platform.transient_retry.latency import attempt_estimate

logger = logging.getLogger(__name__)


async def with_transient_retry(call: Callable[..., Awaitable[Any]], **kwargs: Any) -> Any:
    """Await *call* with backed-off retries; one exhausted call may then use its fallback model.

    Anything not transient, anything the phase budget cannot fund, and any model
    with no fallback fails as before. A fallback applies to this call alone and
    gets its own retries (:mod:`.fallback`).

    :param call: The async provider call to run.
    :param kwargs: Its keyword arguments, passed through unchanged.
    :returns: Whatever *call* returns.
    :raises BaseException: The failure of the last attempt made.
    """
    fallback = fallback_model_for(str(kwargs.get("model", "")))
    # Priced by what the fallback has measurably taken, when anything is (T-20260913-082).
    measured = attempt_estimate(fallback) if fallback else None
    value, failure, elapsed, stopped = await ladder(call, kwargs, (fallback is not None, measured))
    if failure is None:
        return value
    # A hand-over may follow a timeout at the reserving ceiling, which is not transient (T-085).
    if (stopped == BUDGET_SPENT or fallback is None
            or (stopped != HAND_OVER and not is_transient(failure))
            or not fits_in_budget(elapsed if measured is None else measured, 0.0)):
        raise failure
    note_retry(failure)
    note_fallback(fallback)
    logger.warning("transient_retry: model=%s %s (%s); this call falls back to %s.",
                   kwargs.get("model"), "handed its last funded attempt over" if stopped == HAND_OVER
                   else f"exhausted {MAX_TRANSIENT_RETRIES} retries", type(failure).__name__, fallback)
    value, failure, _, _ = await ladder(call, {**kwargs, "model": fallback})
    if failure is None:
        return value
    raise failure


__all__ = ["with_transient_retry", "backoff_seconds", "MAX_TRANSIENT_RETRIES",
           "TRANSIENT_BACKOFF_SECONDS", "TRANSIENT_BACKOFF_CAP_SECONDS"]
