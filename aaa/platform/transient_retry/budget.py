"""Whether the phase budget funds another attempt, and why a retry ladder stops early."""
from __future__ import annotations

#: Why a ladder stopped before its last retry: the phase could fund no further
#: attempt at all, or only one — which goes to the call's fallback model instead.
BUDGET_SPENT, HAND_OVER = "budget_spent", "hand_over"


def fits_in_budget(elapsed: float, wait: float) -> bool:
    """Whether the current phase has room to wait *wait* and make another attempt costing *elapsed*.

    :param elapsed: Seconds the failed attempt took.
    :param wait: The backoff before the next attempt.
    :returns: True when no phase deadline is bound, or when the backoff plus
        another attempt of the same cost still fits inside what is left.
    """
    from aaa.platform.phase_budget import remaining_seconds

    remaining = remaining_seconds()
    if remaining is None:
        return True
    return remaining > wait + elapsed


_STOP_NOTE = {BUDGET_SPENT: "the phase budget cannot fund another attempt",
              HAND_OVER: "the phase budget funds the fallback model's attempt, so it gets the time"}


def _stop_reason(elapsed: float, wait: float, has_fallback: bool,
                 measured: float | None) -> str:
    """Whether the budget ends this ladder now, and why (``""`` to retry).

    :param elapsed: The failed attempt's seconds — the estimate for retrying this model.
    :param wait: The backoff before a retry.
    :param has_fallback: The call maps to a fallback model.
    :param measured: That model's measured successful-attempt cost, or ``None``. Unmeasured,
        the fallback is priced like a retry (``elapsed`` plus the backoff) — conservative,
        since an instant failure says nothing of what a delivered answer costs. Measured, it
        is priced at what it has actually taken (T-20260913-082).
    """
    if not has_fallback:
        return "" if fits_in_budget(elapsed, wait) else BUDGET_SPENT
    cost = elapsed if measured is None else measured
    if fits_in_budget(elapsed, wait + cost):
        return ""
    return HAND_OVER if fits_in_budget(cost, wait if measured is None else 0.0) else BUDGET_SPENT


#: Keyword a capped attempt carries to ``flex_retry.one_call``; popped before LiteLLM sees it.
ATTEMPT_CEILING = "_attempt_ceiling"


def capped(kwargs: dict, reserve: float | None) -> dict:
    """*kwargs* with this attempt's ceiling set to the time left minus *reserve*.

    Inside a phase the client ceiling is the whole remaining budget, so a hung primary
    attempt spent the time reserved for the fallback (case 02, Phase 4, 2026-09-13:
    an overload at 107.7 s, then a retry that hung to the phase's end; T-20260913-085).

    :param reserve: The fallback attempt's price, or ``None`` when nothing is reserved.
    """
    from aaa.platform.phase_budget import remaining_seconds

    left = remaining_seconds()
    if reserve is None or left is None or left - reserve <= 0:
        return kwargs
    return {**kwargs, ATTEMPT_CEILING: left - reserve}


def hit_cap(kwargs: dict, exc: BaseException, has_fallback: bool = False) -> bool:
    """Whether *exc* is a timeout that should go to the fallback rather than end the call.

    Inside a phase: the capped attempt reached the ceiling that reserves the fallback's
    time (T-085). Outside one there is no budget to protect: a hung call with a fallback
    hands over instead of ending, since the caller would only ask the same model again
    (Orchestrator decide call, clean loop case 02, 2026-09-13; T-20260913-089).
    """
    if "Timeout" not in type(exc).__name__:
        return False
    from aaa.platform.phase_budget import remaining_seconds

    return ATTEMPT_CEILING in kwargs or (has_fallback and remaining_seconds() is None)
