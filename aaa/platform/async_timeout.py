"""Run an async coroutine from sync code with an *effective* wall-clock timeout.

The phase-node wrappers previously used ``with ThreadPoolExecutor() as pool: …
.result(timeout=N)``. That pattern is unsafe: when ``.result(timeout=N)`` raises
``TimeoutError``, the ``with`` block's ``__exit__`` calls ``pool.shutdown(wait=True)``,
which **blocks until the hung worker thread finishes** — so a stalled LLM call could
wedge the whole pipeline indefinitely (observed: a ~77-minute hang).

``run_coro_blocking`` shuts the pool down with ``wait=False, cancel_futures=True`` in
a ``finally``, so the ``TimeoutError`` propagates immediately and the caller is never
blocked. Bounded failure beats an infinite hang.

**Fix 38 (finding R5): abandoning is not cancelling.** ``cancel_futures=True`` cancels
futures that have not *started*; a running one is left to finish. The coroutine inside
it kept going, the HTTP request stayed open, and the provider billed the whole reply
into a phase that had stopped listening — case 01 #004 returned 5,761 good characters
at 216.8 s into a 120 s budget, case 03 #040 returned 11,480 at 347.8 s into 180 s.
Across the five cases that was **22 calls and 236,182 prompt tokens paid for and
discarded**.

The deadline now lives *inside* the worker's own event loop, where there is a task to
cancel. :func:`asyncio.wait_for` cancels it on expiry, the cancellation propagates
into the HTTP client, the connection closes, and the request stops. The outer
``.result()`` guard is kept — with a small grace period — for the one case the inner
timeout cannot handle: a loop so wedged that it never processes the cancellation. That
falls back to exactly the old behaviour, which is the behaviour that must never hang.

**What this is *not*.** The backlog asks whether a late reply should be *used* rather
than cancelled — case 01 #004's artefact was good, and throwing it away is a real loss.
That was the more valuable repair when the backlog was written. It is not any more, and
the reason is fixes 37 and 46: the client ceiling is now the phase's *remaining budget*
and it is no longer silently tripled underneath, so the transport gives up at the same
moment the runner does. A reply that arrives well after the deadline with good content
in it is a situation those two fixes largely removed — re-measured, the population of
abandoned calls falls from **22 to 1**. Building a mechanism to rescue a call that no
longer happens would be paying for the old world.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import contextvars
from collections.abc import Coroutine
from typing import Any

# Worker threads are abandoned (not killed) on timeout, so cap how many can
# accumulate across a single engagement before we stop spawning new ones.
_MAX_WORKERS = 1

#: Seconds the outer guard waits beyond the inner deadline before giving up on the
#: worker entirely. Long enough for a cancelled task to unwind its HTTP client and
#: for ``asyncio.run`` to close the loop; short enough that a wedged loop still
#: fails fast. The outer guard is the fallback, not the mechanism.
CANCEL_GRACE_SECONDS: float = 5.0


async def _bounded(coro: Coroutine[Any, Any, Any], timeout: float) -> Any:
    """Await *coro*, cancelling it at *timeout* rather than merely leaving it.

    Before this loop closes, LiteLLM's callbacks queued on it are run
    (:func:`aaa.observability.tracing.drain_llm_callbacks`): they carry the
    Langfuse generation for every call the coroutine made, and a queue left
    behind on a closed loop is a trace that never arrives.

    :param coro: The coroutine to run.
    :param timeout: Seconds before the task is cancelled.
    :raises TimeoutError: The task did not finish and was cancelled.
    """
    try:
        return await asyncio.wait_for(coro, timeout)
    finally:
        from aaa.observability.tracing import drain_llm_callbacks
        from aaa.platform.loop_clients import close_loop_llm_clients, close_loop_sessions

        await drain_llm_callbacks()
        # This loop's HTTP clients and sessions close here, not later on another loop
        # (T-088 cached clients; T-093 any session bound to this loop).
        await close_loop_llm_clients()
        await close_loop_sessions()


def run_coro_blocking(coro: Coroutine[Any, Any, Any], timeout: float) -> Any:
    """Run *coro* to completion in a worker thread, bounded by *timeout* seconds.

    Copies the caller's ``contextvars.Context`` into the worker thread first —
    ``ThreadPoolExecutor`` does not do this automatically, so bindings such as
    the Langfuse session id (:mod:`aaa.observability.trace_context`) and the
    phase deadline (:mod:`aaa.platform.phase_budget`) would otherwise silently
    vanish across the thread hop.

    The deadline is enforced *inside* the worker's event loop so the task is
    **cancelled** rather than abandoned (fix 38); the outer ``.result()`` guard
    remains as a fallback against a loop that never processes the cancellation.

    :raises TimeoutError: The coroutine did not finish in time. Raised whether
        the inner cancellation or the outer guard fired, so callers cannot tell
        — and do not need to tell — which bound stopped it.
    """
    ctx = contextvars.copy_context()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS)
    try:
        return pool.submit(
            ctx.run, asyncio.run, _bounded(coro, timeout)
        ).result(timeout=timeout + CANCEL_GRACE_SECONDS)
    finally:
        # Non-blocking: do not wait on a thread that may be stuck in a hung call.
        pool.shutdown(wait=False, cancel_futures=True)


__all__ = ["CANCEL_GRACE_SECONDS", "run_coro_blocking"]
