"""Fix 39 — one bounded retry past a transient provider failure (R7, R13).

Both branches: a transient failure is retried and the retry's outcome is what
the caller sees; anything else — and anything the phase budget cannot fund —
fails exactly as it did before the fix.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from aaa.platform.phase_budget import bind_phase_deadline
from aaa.platform.transient_retry import (
    MAX_TRANSIENT_RETRIES,
    TRANSIENT_BACKOFF_CAP_SECONDS,
    TRANSIENT_BACKOFF_SECONDS,
    backoff_seconds,
    is_transient,
    record_attempts,
    with_transient_retry,
)


class _ServiceUnavailableError(Exception):
    """The shape litellm raises: the run's five 503s, by type name."""


class _TimeoutError(Exception):
    """``litellm.Timeout`` — already spent its ceiling, so never retried."""


def _overloaded() -> _ServiceUnavailableError:
    """The verbatim message from the 2026-09-03 run's five failed calls."""
    return _ServiceUnavailableError(
        "litellm.ServiceUnavailableError: ServiceUnavailableError: "
        "Nvidia_nimException - Service temporarily overloaded")


@pytest.fixture(autouse=True)
def _no_real_backoff(monkeypatch):
    """Keep the suite fast; the backoff itself is asserted separately."""
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())


# --------------------------------------------------------------------------- #
# what counts as transient
# --------------------------------------------------------------------------- #

def test_the_runs_own_five_failures_are_transient():
    assert is_transient(_overloaded())


def test_a_timeout_is_not_transient():
    """R1 would be made worse, not better, by retrying a spent budget."""
    assert not is_transient(_TimeoutError(
        "litellm.Timeout: APITimeoutError - Request timed out. "
        "Error_str: Request timed out. - timeout value=120.0, time taken=186.98 seconds"))


def test_a_4xx_is_not_transient():
    assert not is_transient(PermissionError("401 Invalid API key"))
    assert not is_transient(ValueError("400 BadRequestError - malformed messages"))


def test_an_unrecognised_failure_keeps_todays_terminal_behaviour():
    """The allow-list's safe default: unknown means terminal."""
    assert not is_transient(RuntimeError("something nobody has seen before"))


# --------------------------------------------------------------------------- #
# the retry itself
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_a_transient_failure_is_retried_and_the_retry_is_what_the_caller_sees():
    calls = {"n": 0}

    async def _fails_once(**_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _overloaded()
        return "the reply"

    assert await with_transient_retry(_fails_once, model="m") == "the reply"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_retries_are_bounded_and_the_last_failure_is_re_raised():
    """Nothing is fabricated: after the last retry the failure reaches the caller."""
    calls = {"n": 0}

    async def _always_fails(**_kwargs):
        calls["n"] += 1
        raise _overloaded()

    with pytest.raises(_ServiceUnavailableError):
        await with_transient_retry(_always_fails, model="m")
    assert calls["n"] == MAX_TRANSIENT_RETRIES + 1


@pytest.mark.asyncio
async def test_a_pool_that_fails_several_times_in_a_row_is_still_recovered():
    """The free route failed instantly twice two seconds apart; a third try waits longer."""
    calls = {"n": 0}

    async def _fails_three_times(**_kwargs):
        calls["n"] += 1
        if calls["n"] <= 3:
            raise _overloaded()
        return "the reply"

    assert await with_transient_retry(_fails_three_times, model="m") == "the reply"
    assert calls["n"] == 4


def test_the_backoff_grows_exponentially_with_a_floor_and_a_cap():
    lows = [backoff_seconds(n, draw=lambda: 0.0) for n in range(6)]
    highs = [backoff_seconds(n, draw=lambda: 0.999999) for n in range(6)]
    assert lows[:4] == [1.0, 2.0, 4.0, 8.0]
    assert all(a < b for a, b in zip(highs, highs[1:4]))
    assert max(highs) <= TRANSIENT_BACKOFF_CAP_SECONDS


@pytest.mark.asyncio
async def test_a_non_transient_failure_is_not_retried():
    calls = {"n": 0}

    async def _auth_fail(**_kwargs):
        calls["n"] += 1
        raise PermissionError("401 Invalid API key")

    with pytest.raises(PermissionError):
        await with_transient_retry(_auth_fail, model="m")
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_a_first_attempt_success_costs_nothing_extra():
    calls = {"n": 0}

    async def _ok(**_kwargs):
        calls["n"] += 1
        return "the reply"

    assert await with_transient_retry(_ok, model="m") == "the reply"
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_the_backoff_is_waited_before_the_retry(monkeypatch):
    slept = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", slept)
    calls = {"n": 0}

    async def _fails_once(**_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _overloaded()
        return "the reply"

    await with_transient_retry(_fails_once, model="m")
    slept.assert_awaited_once()
    waited = slept.await_args.args[0]
    assert TRANSIENT_BACKOFF_SECONDS / 2 <= waited <= TRANSIENT_BACKOFF_SECONDS


# --------------------------------------------------------------------------- #
# the budget rule
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_an_unbound_deadline_means_no_budget_to_respect():
    """The Verifier and the Orchestrator run outside any phase timeout."""
    calls = {"n": 0}

    async def _fails_once(**_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _overloaded()
        return "the reply"

    assert await with_transient_retry(_fails_once, model="m") == "the reply"


@pytest.mark.asyncio
async def test_a_spent_phase_budget_declines_the_retry():
    """ScopeAgent's 503 landed 62 s past a 120 s budget — nothing to retry into."""
    calls = {"n": 0}

    async def _always_fails(**_kwargs):
        calls["n"] += 1
        raise _overloaded()

    with bind_phase_deadline(0.001):
        with pytest.raises(_ServiceUnavailableError):
            await with_transient_retry(_always_fails, model="m")
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_a_phase_with_room_funds_the_retry():
    calls = {"n": 0}

    async def _fails_once(**_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _overloaded()
        return "the reply"

    with bind_phase_deadline(600):
        assert await with_transient_retry(_fails_once, model="m") == "the reply"
    assert calls["n"] == 2


# --------------------------------------------------------------------------- #
# the trail records which it was
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_a_recovered_call_is_distinguishable_from_a_clean_one():
    async def _fails_once(**_kwargs):
        if not getattr(_fails_once, "hit", False):
            _fails_once.hit = True
            raise _overloaded()
        return "the reply"

    async def _ok(**_kwargs):
        return "the reply"

    with record_attempts() as clean:
        await with_transient_retry(_ok, model="m")
    assert clean == []

    with record_attempts() as recovered:
        await with_transient_retry(_fails_once, model="m")
    assert len(recovered) == 1
    assert "Service temporarily overloaded" in recovered[0]
