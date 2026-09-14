"""phase_budget — how long a phase gets, and how much of it is left.

Two halves, which arrived as two fixes:

* :mod:`.deadline` — **fix 18.** The wall-clock deadline the current phase is
  running under, bound around the dispatch and readable from anywhere below it,
  so the ReAct loop can decline a retrieval round it has no time to finish.
* :mod:`.observed` and :mod:`.sizing` — **fix 34.** How large that budget should
  be in the first place. It was a literal (``120`` for Phase 1, ``180`` for the
  rest) resting on a measurement of a different provider that nothing ever took
  again; in the 2026-09-03 run those literals cost four of five cases their
  Phase 1. It is now derived from what this process has just watched a phase
  agent's calls cost, floored, capped, and logged with the reading that produced
  it.

The two halves meet in one sentence: **the same measurement that decides whether
another round fits now also decides how much room there was to fit it in.**
"""
from aaa.platform.phase_budget.deadline import (  # noqa: F401
    bind_phase_deadline,
    deadline_is_bound,
    remaining_seconds,
)
from aaa.platform.phase_budget.observed import (  # noqa: F401
    observe,
    observe_failure,
    reset,
    slowest_call,
    slowest_failure,
)
from aaa.platform.phase_budget.sizing import (  # noqa: F401
    AGENT_MIN_PHASE_SECONDS,
    CALLS_PER_PHASE,
    MAX_PHASE_SECONDS,
    MIN_PHASE_SECONDS,
    phase_timeout,
)

__all__ = [
    "bind_phase_deadline",
    "remaining_seconds",
    "deadline_is_bound",
    "observe",
    "observe_failure",
    "slowest_call",
    "slowest_failure",
    "reset",
    "phase_timeout",
    "CALLS_PER_PHASE",
    "MIN_PHASE_SECONDS",
    "MAX_PHASE_SECONDS",
    "AGENT_MIN_PHASE_SECONDS",
]
