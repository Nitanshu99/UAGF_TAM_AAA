"""run_coro_blocking: effective wall-clock timeout that does not hang on stalls."""
from __future__ import annotations

import asyncio
import concurrent.futures
import time
from contextvars import ContextVar

import pytest

from aaa.platform.async_timeout import run_coro_blocking


def test_returns_result_within_timeout():
    """A coroutine that finishes well inside the timeout returns its result."""
    async def work():
        """Sleep briefly, then return a sentinel value."""
        await asyncio.sleep(0.01)
        return 7
    assert run_coro_blocking(work(), timeout=5) == 7


def test_raises_timeout_without_blocking():
    """A stalled coroutine raises TimeoutError promptly, not after the stall."""
    async def stall():
        """Sleep far longer than the caller's timeout."""
        await asyncio.sleep(30)  # longer than the timeout
        return 1

    t0 = time.monotonic()
    with pytest.raises(concurrent.futures.TimeoutError):
        run_coro_blocking(stall(), timeout=0.3)
    elapsed = time.monotonic() - t0
    # The key property: we return promptly at the timeout, NOT after the stall.
    assert elapsed < 5, f"timeout did not return promptly (elapsed={elapsed:.1f}s)"


def test_propagates_coroutine_exception():
    """An exception raised inside the coroutine propagates to the caller."""
    async def boom():
        """Raise immediately."""
        raise ValueError("nope")
    with pytest.raises(ValueError, match="nope"):
        run_coro_blocking(boom(), timeout=5)


def test_contextvars_survive_the_worker_thread():
    """ThreadPoolExecutor does not copy contextvars by default — this must."""
    var: ContextVar[str] = ContextVar("var", default="unset")
    token = var.set("bound-in-caller")
    try:
        async def read_var():
            return var.get()
        assert run_coro_blocking(read_var(), timeout=5) == "bound-in-caller"
    finally:
        var.reset(token)
