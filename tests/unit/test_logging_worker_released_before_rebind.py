"""T-20260913-101: LiteLLM's logging worker is stopped on its loop before another loop takes it.

LiteLLM re-binds its global worker to a new loop by dropping the old task's only
reference; the pending task was then collected with "Task was destroyed but it is
pending!" each time a phase loop made its first call after the Orchestrator's.
"""
from __future__ import annotations

import asyncio
import gc
import logging
from types import SimpleNamespace

import pytest

from aaa.observability.tracing import drain_llm_callbacks
from aaa.observability.tracing.worker import release_logging_worker
from aaa.platform.async_timeout import run_coro_blocking

worker_mod = pytest.importorskip("litellm.litellm_core_utils.logging_worker")
_WORKER = worker_mod.GLOBAL_LOGGING_WORKER


async def _call(ran: list[str], tag: str) -> None:
    """Queue a callback the way a LiteLLM call does, and let it run."""
    async def callback() -> None:
        ran.append(tag)
    _WORKER.ensure_initialized_and_enqueue(callback())
    await asyncio.sleep(0.05)


def test_a_phase_loop_after_the_orchestrator_destroys_no_pending_task(caplog) -> None:
    """The hop's drain releases the worker; the phase loop's call re-binds nothing pending."""
    ran: list[str] = []

    async def orchestrator() -> None:
        await _call(ran, "orchestrator")
        await drain_llm_callbacks()
        run_coro_blocking(_call(ran, "phase"), 10)
        gc.collect()
        await _call(ran, "after the hop")  # restarted on this loop, and it still runs

    with caplog.at_level(logging.ERROR, logger="asyncio"):
        asyncio.run(orchestrator())
        gc.collect()
    assert "Task was destroyed but it is pending" not in caplog.text
    assert ran == ["orchestrator", "phase", "after the hop"]


def test_another_loops_worker_is_left_alone() -> None:
    """A worker bound elsewhere is not this loop's to cancel."""
    stopped: list[bool] = []

    async def stop() -> None:
        stopped.append(True)

    other = SimpleNamespace(_worker_task=SimpleNamespace(done=lambda: False),
                            _bound_loop=object(), stop=stop)
    assert asyncio.run(release_logging_worker(other)) is False and not stopped
