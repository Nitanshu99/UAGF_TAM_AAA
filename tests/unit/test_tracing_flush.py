"""Unit tests for flush_llm_tracing (aaa.observability.tracing.flush)."""
from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from aaa.observability import tracing


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    """Reset the idempotency latch and stub litellm around every test."""
    tracing.reset_llm_tracing_state()
    stub = types.SimpleNamespace(success_callback=[], failure_callback=[])
    monkeypatch.setitem(sys.modules, "litellm", stub)
    yield
    tracing.reset_llm_tracing_state()


async def test_flush_is_noop_when_tracing_off():
    """Nothing configured → nothing imported, nothing awaited."""
    await tracing.flush_llm_tracing()  # must not raise with the litellm stub


async def test_flush_drains_worker_and_exports_spans(monkeypatch):
    """Configured → the LiteLLM logging queue is drained and every OTEL provider flushed."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    tracing.configure_llm_tracing()

    drained = []

    class _Queue:
        """asyncio.Queue stand-in that empties on flush."""

        pending = 1

        def empty(self):
            """True once flushed."""
            return self.pending == 0

    class _Worker:
        """Stand-in for litellm's GLOBAL_LOGGING_WORKER."""

        _queue: Any = _Queue()
        _running_tasks: set = set()

        async def flush(self):
            """Record that the queue was drained."""
            drained.append("queue")
            self._queue.pending = 0

    class _Provider:
        """Stand-in for an OTEL TracerProvider."""

        def __init__(self):
            self.flushed = 0

        def force_flush(self, timeout_millis=0):
            """Count exports; the real one pushes the span batch."""
            self.flushed += 1

    provider = _Provider()
    stub = sys.modules["litellm"]
    setattr(stub, "callbacks", [types.SimpleNamespace(tracer_provider=provider)])
    stub.success_callback.append(types.SimpleNamespace(tracer_provider=provider))
    core = types.ModuleType("litellm.litellm_core_utils")
    worker_mod = types.ModuleType("litellm.litellm_core_utils.logging_worker")
    setattr(worker_mod, "GLOBAL_LOGGING_WORKER", _Worker())
    monkeypatch.setitem(sys.modules, "litellm.litellm_core_utils", core)
    monkeypatch.setitem(sys.modules, "litellm.litellm_core_utils.logging_worker", worker_mod)

    await tracing.flush_llm_tracing()

    assert drained == ["queue"]
    assert provider.flushed == 1  # same provider reached twice, flushed once
