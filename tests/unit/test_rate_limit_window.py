"""FixedWindowLimiter fixed-window wait/no-wait behaviour."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from aaa.platform.rate_limit.limiter import FixedWindowLimiter


def _fake_clock(values):
    """Return a zero-arg callable yielding *values* in order, injected as clock=."""
    times = iter(values)
    return lambda: next(times)


@pytest.mark.asyncio
async def test_calls_below_cap_never_check_the_clock(monkeypatch):
    """Calls before the Nth (cap-reaching) request never sleep."""
    sleep = AsyncMock()
    monkeypatch.setattr("aaa.platform.rate_limit.limiter.asyncio.sleep", sleep)
    limiter = FixedWindowLimiter(max_requests=3, window_seconds=60.0,
                                  clock=_fake_clock([0.0]))

    await limiter.acquire()
    await limiter.acquire()

    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_cap_reached_before_window_elapses_waits_remainder(monkeypatch):
    """Reaching the cap with time left in the window sleeps exactly the remainder."""
    sleep = AsyncMock()
    monkeypatch.setattr("aaa.platform.rate_limit.limiter.asyncio.sleep", sleep)
    limiter = FixedWindowLimiter(max_requests=2, window_seconds=60.0,
                                  clock=_fake_clock([0.0, 45.0, 45.0]))

    await limiter.acquire()  # count -> 1, under cap
    await limiter.acquire()  # count -> 2, cap reached: elapsed=45 -> sleep(15)

    sleep.assert_awaited_once()
    assert sleep.await_args is not None
    assert sleep.await_args.args[0] == pytest.approx(15.0)


@pytest.mark.asyncio
async def test_cap_reached_after_window_elapsed_does_not_wait(monkeypatch):
    """If the window is already over when the cap is reached, no sleep happens."""
    sleep = AsyncMock()
    monkeypatch.setattr("aaa.platform.rate_limit.limiter.asyncio.sleep", sleep)
    limiter = FixedWindowLimiter(max_requests=2, window_seconds=60.0,
                                  clock=_fake_clock([0.0, 61.0, 61.0]))

    await limiter.acquire()
    await limiter.acquire()

    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_window_resets_after_cap_so_a_third_call_stays_under(monkeypatch):
    """After the reset, the count restarts, so the next call doesn't re-trigger."""
    sleep = AsyncMock()
    monkeypatch.setattr("aaa.platform.rate_limit.limiter.asyncio.sleep", sleep)
    limiter = FixedWindowLimiter(max_requests=2, window_seconds=60.0,
                                  clock=_fake_clock([0.0, 61.0, 61.0]))

    await limiter.acquire()  # count -> 1
    await limiter.acquire()  # count -> 2, cap reached, resets to count=0
    await limiter.acquire()  # count -> 1, under new cap

    sleep.assert_not_awaited()
