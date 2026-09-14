"""Flush the LLM-tracing pipeline before a process exits.

LiteLLM runs success/failure callbacks on a background queue and the OTEL
exporter batches spans, so a process that exits right after its last LLM
call (``aaa.cli run``, the mock-case runner, the probe) otherwise reaches
interpreter shutdown with the ``langfuse_otel`` callback still queued —
observed as ``cannot schedule new futures after interpreter shutdown`` and a
trace that never arrives. :func:`flush_llm_tracing` is awaited once per
engagement by the Orchestrator runner and is a no-op when tracing is off.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from aaa.observability.tracing.state import is_llm_tracing_configured

logger = logging.getLogger(__name__)


async def _drain(worker: Any, rounds: int = 50, pause: float = 0.02) -> None:
    """Wait for LiteLLM's queued callbacks to finish, yielding first.

    LiteLLM enqueues the success handler from a task it schedules *after* the
    awaited call returns, so a flush issued immediately finds no queue at all
    (observed: ``queue: None`` right after the call, one item a moment later).
    Each round yields to the loop, then ``flush()`` — the queue's ``join()`` —
    which returns only once every dequeued callback has run to completion.

    :param worker: LiteLLM's ``GLOBAL_LOGGING_WORKER``.
    :param rounds: Upper bound on yield/flush rounds (default ≈ 1 s idle).
    :param pause: Seconds to yield per round.
    """
    for round_no in range(rounds):
        await asyncio.sleep(pause)
        queue = worker._queue  # pylint: disable=protected-access  # the only handle LiteLLM exposes
        bound = getattr(worker, "_bound_loop", None)
        if bound is not None and bound is not asyncio.get_running_loop():
            return  # the queue belongs to another loop: nothing queued here, and join() would hang
        if queue is None:
            if round_no >= 5:  # nothing was ever enqueued: no LLM call in this process
                return
            continue
        try:
            # Bounded by LiteLLM's own per-callback ceiling: a stuck callback must not hold a phase.
            await asyncio.wait_for(worker.flush(), timeout=getattr(worker, "timeout", None))
        except asyncio.TimeoutError:
            logger.warning("LiteLLM logging queue did not drain within %ss.", worker.timeout)
            return
        if queue.empty() and not worker._running_tasks:  # pylint: disable=protected-access
            return


async def drain_llm_callbacks() -> None:
    """Run LiteLLM's queued success/failure callbacks on the *current* loop.

    The callbacks are queued on the event loop the call was made on. A phase
    agent runs on a worker thread whose loop closes the moment its coroutine
    returns (:func:`aaa.platform.async_timeout.run_coro_blocking`), and a
    callback still queued there is lost — LiteLLM's carry-over to the next loop
    fails with ``task_done() called too many times``. The 2026-09-12 minimax run
    reached Langfuse with 58 of 72 generations: every Orchestrator and Verifier
    call (main loop) arrived, every phase agent's call (worker loop) did not.
    Bounded at about a second of idling. It runs whether or not tracing is on:
    LiteLLM queues its own logging callbacks for every call, and with tracing off
    they were left on the closing loop and later raised ``task_done() called too
    many times`` against a queue re-bound to the next loop (T-20260913-083).

    :returns: None
    """
    try:
        from litellm.litellm_core_utils.logging_worker import GLOBAL_LOGGING_WORKER

        from aaa.observability.tracing.worker import release_logging_worker

        await _drain(GLOBAL_LOGGING_WORKER)
        # Then stop its task here, so the next loop's re-bind drops nothing pending (T-101).
        await release_logging_worker(GLOBAL_LOGGING_WORKER)
    except Exception as exc:  # noqa: BLE001 — never let flushing break a run
        logger.warning("LiteLLM logging queue flush failed: %s", exc)


async def flush_llm_tracing() -> None:
    """Drain LiteLLM's async logging queue, then export buffered OTEL spans.

    :returns: None
    """
    await drain_llm_callbacks()
    if not is_llm_tracing_configured():
        return
    import litellm  # type: ignore

    seen: set[int] = set()
    for callback in [*getattr(litellm, "callbacks", []), *litellm.success_callback]:
        provider = getattr(callback, "tracer_provider", None)
        if provider is not None and id(provider) not in seen and hasattr(provider, "force_flush"):
            seen.add(id(provider))
            provider.force_flush(timeout_millis=10_000)
