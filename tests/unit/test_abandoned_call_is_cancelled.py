"""Fix 38 — an abandoned call is cancelled, not merely left running (finding R5).

`cancel_futures=True` cancels futures that have not *started*; a running one is
left to finish. So the coroutine kept going, the HTTP request stayed open, and the
provider billed a reply into a phase that had stopped listening — 22 calls and
236,182 prompt tokens across the five cases of the 2026-09-03 run.

Re-measured after fixes 34 and 37, that population is **1**. The mechanism is fixed
anyway, because the acceptance is about the mechanism and because fix 48 now runs
three critiques at once, so an abandonment can happen threefold.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from aaa.platform.async_timeout import CANCEL_GRACE_SECONDS, run_coro_blocking


class _Call:
    """Stands in for an HTTP request: records whether it was cancelled or ran on."""

    def __init__(self, duration: float) -> None:
        self.duration = duration
        self.started = False
        self.cancelled = False
        self.completed = False
        self.closed = False

    async def __call__(self):
        self.started = True
        try:
            await asyncio.sleep(self.duration)
            self.completed = True
            return "a reply"
        except asyncio.CancelledError:
            self.cancelled = True
            raise
        finally:
            # what an HTTP client's `finally`/`aclose` would do
            self.closed = True


# --------------------------------------------------------------------------- #
# cancelled at the transport, not abandoned
# --------------------------------------------------------------------------- #

def test_an_overrunning_call_is_cancelled():
    call = _Call(duration=5.0)
    with pytest.raises(TimeoutError):
        run_coro_blocking(call(), timeout=0.1)
    assert call.started
    assert call.cancelled, "the task was cancelled, not left to finish"
    assert not call.completed


def test_the_client_gets_to_close_its_connection():
    """No lingering session: the `finally` runs, because cancellation reaches it."""
    call = _Call(duration=5.0)
    with pytest.raises(TimeoutError):
        run_coro_blocking(call(), timeout=0.1)
    assert call.closed


def test_the_caller_is_not_made_to_wait_for_the_call_it_gave_up_on():
    call = _Call(duration=30.0)
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        run_coro_blocking(call(), timeout=0.1)
    elapsed = time.monotonic() - started
    assert elapsed < 2.0, f"{elapsed:.2f}s — the point is bounded failure"


# --------------------------------------------------------------------------- #
# a completed call is unaffected
# --------------------------------------------------------------------------- #

def test_a_call_that_finishes_in_time_is_untouched():
    call = _Call(duration=0.01)
    assert run_coro_blocking(call(), timeout=5.0) == "a reply"
    assert call.completed
    assert not call.cancelled


def test_the_result_is_returned_not_swallowed():
    async def _work():
        return {"summary": "done"}
    assert run_coro_blocking(_work(), timeout=5.0) == {"summary": "done"}


def test_an_exception_inside_the_call_still_propagates():
    async def _boom():
        raise ValueError("provider said no")
    with pytest.raises(ValueError, match="provider said no"):
        run_coro_blocking(_boom(), timeout=5.0)


# --------------------------------------------------------------------------- #
# the context still crosses the thread, and the outer guard still exists
# --------------------------------------------------------------------------- #

def test_the_phase_deadline_still_crosses_the_thread_hop():
    """Fix 18 and fix 37 both read this contextvar from inside the worker."""
    from aaa.platform.phase_budget import bind_phase_deadline, remaining_seconds

    async def _read():
        return remaining_seconds()

    with bind_phase_deadline(300):
        left = run_coro_blocking(_read(), timeout=5.0)
    assert left is not None and 299.0 < left <= 300.0


def test_the_outer_guard_is_still_there_as_a_fallback():
    """A loop that never processes the cancellation must not wedge the caller."""
    assert CANCEL_GRACE_SECONDS > 0


def test_the_timeout_is_raised_as_a_timeout_whichever_bound_fired():
    """Fix 35 classifies a lost phase by the exception's type name."""
    from aaa.agents.tier1.phases.verification.no_report import _classify

    call = _Call(duration=5.0)
    try:
        run_coro_blocking(call(), timeout=0.1)
    except Exception as exc:  # noqa: BLE001
        assert isinstance(exc, TimeoutError)
        assert _classify(exc) == "budget"
    else:
        pytest.fail("expected a timeout")
