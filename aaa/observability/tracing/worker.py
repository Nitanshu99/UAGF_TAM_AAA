"""Stop LiteLLM's logging worker on the loop it runs on, before another loop takes it over.

LiteLLM's ``GLOBAL_LOGGING_WORKER`` runs ``_worker_loop`` as a task on the loop of
the call that first queued a callback. When a call on a different loop queues the
next one, LiteLLM re-binds the worker by setting ``_worker_task = None`` without
cancelling the old task. That task still waits on the old queue, nothing refers to
it any more, and garbage collection reports ``Task was destroyed but it is
pending!`` — every time a phase's worker loop made its first call after the
Orchestrator's (clean loop, case 05 and case 02, 2026-09-13; T-20260913-101;
reproduced on litellm 1.86.0 and 1.100.1). Stopped with LiteLLM's own ``stop()``
on its own loop, it is cancelled and awaited there, and the next call restarts it
(``ensure_initialized_and_enqueue`` calls ``start()``).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def release_logging_worker(worker: Any) -> bool:
    """Stop *worker* if its task belongs to the running loop; leave any other loop's alone.

    :param worker: LiteLLM's ``GLOBAL_LOGGING_WORKER``.
    :returns: Whether a running worker task was stopped.
    """
    task = getattr(worker, "_worker_task", None)
    if task is None or task.done() or getattr(worker, "_bound_loop", None) is not (
            asyncio.get_running_loop()):
        return False
    try:
        await worker.stop()
    except Exception as exc:  # noqa: BLE001 — releasing must never break a run
        logger.warning("Stopping LiteLLM's logging worker failed: %s", exc)
        return False
    return True


__all__ = ["release_logging_worker"]
