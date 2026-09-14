"""Close the LiteLLM HTTP clients an event loop created, on that loop, before it closes.

LiteLLM caches async HTTP clients per event loop (``LLMClientCache`` suffixes each key
with ``id(loop)``) for an hour, and ``AsyncHTTPHandler.__del__`` schedules ``close()``
on whichever loop is running when the client is collected. A phase agent runs on a
worker-thread loop that closes when its coroutine returns
(:func:`aaa.platform.async_timeout.run_coro_blocking`), so its clients were later
closed from the orchestrator's loop: ``RuntimeError: … attached to a different loop``
(clean loop, case 02, 2026-09-13; T-20260913-088). Closed here first, a later close
finds nothing left to do.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def close_loop_llm_clients() -> int:
    """Close and forget every cached LiteLLM client bound to the running loop.

    :returns: How many clients were closed.
    """
    try:
        import litellm  # type: ignore
    except ImportError:
        return 0
    cache = getattr(litellm, "in_memory_llm_clients_cache", None)
    entries = getattr(cache, "cache_dict", None)
    if not isinstance(entries, dict):
        return 0
    suffix = f"-{id(asyncio.get_running_loop())}"
    closed = 0
    for key in [k for k in list(entries) if str(k).endswith(suffix)]:
        client = entries.get(key)
        getattr(cache, "_remove_key", entries.pop)(key)
        close = getattr(client, "close", None) or getattr(client, "aclose", None)
        try:
            result = close() if callable(close) else None
            if asyncio.iscoroutine(result):
                await result
            closed += 1
        except Exception as exc:  # noqa: BLE001 — cleanup must never break a phase
            logger.debug("Closing LiteLLM client %s failed: %s", key, exc)
    return closed


async def close_loop_sessions() -> int:
    """Close every live LiteLLM aiohttp session bound to the running loop, cached or not.

    The cache sweep above missed a handler that was not (or no longer) cached, and the
    transport replaces a session bound to another loop without closing it; either way a
    session outlived its loop and was closed later from another one (T-20260913-093).
    Closed here, on its own loop, every later close finds a closed session.

    :returns: How many sessions were closed.
    """
    import gc
    import warnings

    try:
        from litellm.llms.custom_httpx.aiohttp_transport import LiteLLMAiohttpTransport
    except ImportError:
        return 0
    loop = asyncio.get_running_loop()
    # isinstance over every live object touches foreign objects — torch's deprecated
    # module proxies warn on access — so any warning here is about them, not about this
    # scan, and it named this line on every phase (T-20260913-103).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sessions = [getattr(obj, "client", None) for obj in gc.get_objects()
                    if isinstance(obj, LiteLLMAiohttpTransport)]
    closed = 0
    for session in sessions:
        if getattr(session, "_loop", None) is not loop or getattr(session, "closed", True):
            continue
        try:
            await session.close()  # type: ignore[union-attr]
            closed += 1
        except Exception as exc:  # noqa: BLE001 — cleanup must never break a phase
            logger.debug("Closing an aiohttp session failed: %s", exc)
    return closed


__all__ = ["close_loop_llm_clients", "close_loop_sessions"]
