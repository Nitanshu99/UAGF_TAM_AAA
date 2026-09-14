"""What a phase agent's LLM calls actually cost — fix 34 (finding R1).

`timeouts.py` fixed the phase ceiling on a sentence: *"The phase agents keep
120 s deliberately. Their slowest call was 106.3 s."* That was a real
measurement of a different provider under a different load, and **nothing
re-measured it**. In the 2026-09-03 run the same agents' calls ran 39 s to
347.8 s, and Phase 1 — shortest budget, largest payload — was lost in four of
the five cases.

So the measurement stops being a sentence in a docstring and becomes a reading
the process keeps taking. Every LLM call already passes through
:func:`aaa.agents.base.audit.write_audit`, which computes its wall-clock; that
is the whole instrumentation.

**Only calls made inside a bound phase deadline are recorded**, and that one
condition is what makes the sample the right one. The Verifier runs after
``run_agent_on_state`` returns and the Orchestrator's decide loop outside phases
altogether, so neither is inside a binding — and neither should shape a phase's
budget, the Verifier least of all: it carries the largest prompts in the system
(median 131.7 s against a phase agent's 94.6 s) and would inflate every budget
it touched. No agent list is needed to express that, and none can drift.

**The window is bounded and the estimator is the max inside it.** Max, because
that is what :func:`~aaa.tools.evidence_retrieval.rounds.rounds_fit` already
uses one level down, and a budget derived from a median under-funds the half of
calls above it — which is finding R1 restated. Bounded, because a single 347.8 s
outlier must not pin every later phase to the ceiling for the rest of the run:
twenty calls is roughly the last three phases, recent enough to track a provider
whose load has changed and long enough that one quick phase cannot collapse the
budget under the next slow one.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Deque

from aaa.platform.phase_budget.deadline import deadline_is_bound

#: How many recent phase-agent calls the estimate is drawn from. See above.
WINDOW = 20

_lock = threading.Lock()
_recent: Deque[float] = deque(maxlen=WINDOW)
_by_agent: dict[str, Deque[float]] = {}
#: Time-to-error of recent transient failures inside phases, whichever model failed.
_failures: Deque[float] = deque(maxlen=WINDOW)


def observe(agent_name: str, seconds: float) -> None:
    """Record what one phase-agent LLM call cost.

    Silently ignores a call made outside a phase deadline, and a non-positive
    duration: both are readings that say nothing about what a phase costs.

    :param agent_name: ``BaseAgent.name`` of the caller.
    :type agent_name: str
    :param seconds: Wall-clock seconds the call took, retries included.
    :type seconds: float
    """
    if seconds <= 0 or not deadline_is_bound():
        return
    with _lock:
        _recent.append(seconds)
        _by_agent.setdefault(agent_name, deque(maxlen=WINDOW)).append(seconds)


def slowest_call(agent_name: str | None = None) -> float | None:
    """The slowest recent call, for *agent_name* if it has any, else for any phase.

    An agent's own history is preferred because payload size differs sharply by
    phase — Phase 1 assembles 52 kB where Phase 5 assembles a fraction of it —
    but an agent dispatched for the first time is better served by what its
    peers have just measured than by a constant.

    :param agent_name: Agent to prefer, or ``None`` for the pooled reading.
    :type agent_name: str | None
    :returns: Seconds, or ``None`` when nothing has been measured yet.
    :rtype: float | None
    """
    with _lock:
        own = _by_agent.get(agent_name or "")
        if own:
            return max(own)
        return max(_recent) if _recent else None


def observe_failure(seconds: float) -> None:
    """Record how long one transient failure took to arrive, inside a phase deadline.

    A retried attempt spends this before the retry starts; on an overloaded free
    route that was 66–97 s a time (case 05, 2026-09-13; T-20260913-102).

    :param seconds: Wall-clock seconds from the attempt's start to its error.
    """
    if seconds <= 0 or not deadline_is_bound():
        return
    with _lock:
        _failures.append(seconds)


def slowest_failure() -> float | None:
    """The slowest recent transient failure in any phase, or ``None`` when none was seen."""
    with _lock:
        return max(_failures) if _failures else None


def reset() -> None:
    """Forget every measurement. For tests; the process otherwise accumulates."""
    with _lock:
        _recent.clear()
        _by_agent.clear()
        _failures.clear()


__all__ = ["WINDOW", "observe", "observe_failure", "reset", "slowest_call", "slowest_failure"]
