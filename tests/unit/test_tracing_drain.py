"""Unit tests for the LiteLLM logging-queue drain (aaa.observability.tracing.flush._drain)."""
from __future__ import annotations

from typing import Any


async def test_drain_waits_for_a_late_enqueue():
    """A callback enqueued one loop-turn after the call is still drained."""
    import asyncio

    from aaa.observability.tracing import flush as flush_mod

    class _Queue:
        """Minimal asyncio.Queue stand-in."""

        def __init__(self):
            self.items = 1

        def empty(self):
            """True once the worker consumed the item."""
            return self.items == 0

    class _LateWorker:
        """Queue appears only after the first yield, like LiteLLM's create_task."""

        def __init__(self):
            self._queue: Any = None
            self._running_tasks: set = set()
            self.flushes = 0

        async def flush(self):
            """Consume the item."""
            self.flushes += 1
            self._queue.items = 0

    worker = _LateWorker()

    async def _late_enqueue():
        await asyncio.sleep(0)
        worker._queue = _Queue()  # pylint: disable=protected-access

    asyncio.get_running_loop().create_task(_late_enqueue())
    await flush_mod._drain(worker, rounds=20, pause=0.001)  # pylint: disable=protected-access
    assert worker.flushes == 1


async def test_drain_returns_when_nothing_was_enqueued():
    """No LLM call in this process → no queue → bounded early return."""
    from aaa.observability.tracing import flush as flush_mod

    class _IdleWorker:
        """Never starts."""

        _queue = None
        _running_tasks: set = set()

    await flush_mod._drain(_IdleWorker(), rounds=50, pause=0.001)  # pylint: disable=protected-access
