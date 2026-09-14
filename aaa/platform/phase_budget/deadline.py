"""The wall-clock deadline a phase is running under — fix 18.

:func:`aaa.agents.tier1.phases.agent_runner._invoke` runs a phase agent under an
effective timeout (:mod:`aaa.platform.async_timeout`), and that timeout covers
everything the agent does: its deterministic tools, its seed retrieval, and
every LLM call the ReAct loop makes. The loop never knew the number. It ran a
fixed count of expansion rounds and either fitted or did not, and when it did
not the cost was not the round — it was **the whole phase**, because a timed-out
``agent.process`` returns no report at all. That is finding P4: Phase 3's rerun
spent 106.3 s and then 78.5 s against a 180 s budget and produced nothing, so
attempt 1's artefacts stood as the phase's output.

This module hands the loop the one fact it was missing. The binding follows
:mod:`aaa.observability.trace_context` exactly — a context variable set around
the dispatch, read far below it, with no signature threaded through six agents —
and it works across the thread hop for the same reason that one does:
``run_coro_blocking`` copies the caller's context into the worker.

Absent binding means *no deadline*, and that is the correct reading rather than
a fallback. Two of ``_invoke``'s three paths apply no timeout at all, and a unit
test or a direct dispatch has no budget to respect; in those cases the loop
should use its full round ceiling, which is what an unset deadline gives it.

Where the *size* of that budget comes from is :mod:`.sizing` — fix 34.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

#: Absolute ``time.monotonic()`` value at which the current phase's budget ends.
_deadline: ContextVar[float | None] = ContextVar("phase_deadline", default=None)


@contextmanager
def bind_phase_deadline(timeout: float | None) -> Iterator[None]:
    """Bind a deadline *timeout* seconds from now, for the ``with`` block.

    A falsy or non-positive *timeout* binds nothing and leaves any outer
    binding in place — the same narrowing-never-clearing rule
    :func:`~aaa.observability.trace_context.bind_engagement_id` follows, and for
    the same reason: an inner scope that cannot state a budget must not delete
    the budget an outer scope stated.

    :param timeout: Seconds the phase is allowed, or ``None`` to bind nothing.
    :type timeout: float | None
    """
    if not timeout or timeout <= 0:
        yield
        return
    token = _deadline.set(time.monotonic() + float(timeout))
    try:
        yield
    finally:
        _deadline.reset(token)


def remaining_seconds() -> float | None:
    """Seconds left in the current phase's budget.

    :returns: Seconds remaining (may be negative when the budget is already
        spent), or ``None`` when no deadline is bound.
    :rtype: float | None
    """
    deadline = _deadline.get()
    return None if deadline is None else deadline - time.monotonic()


def deadline_is_bound() -> bool:
    """Whether the caller is running inside a phase's wall-clock budget.

    :returns: ``True`` inside a phase dispatch, ``False`` for the Verifier, the
        Orchestrator's decide loop, a unit test or a direct dispatch.
    :rtype: bool
    """
    return _deadline.get() is not None


__all__ = ["bind_phase_deadline", "deadline_is_bound", "remaining_seconds"]
