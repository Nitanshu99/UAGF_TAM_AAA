"""A worker-loop phase call runs LiteLLM's queued callbacks before its loop closes."""
from __future__ import annotations

import asyncio

import pytest

import aaa.observability.tracing as tracing
from aaa.platform.async_timeout import run_coro_blocking


@pytest.fixture
def drained(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Record which event loop the drain ran on."""
    seen: list[int] = []

    async def fake() -> None:
        seen.append(id(asyncio.get_running_loop()))

    monkeypatch.setattr(tracing, "drain_llm_callbacks", fake)
    return seen


def test_the_drain_runs_on_the_worker_loop_after_the_call(drained: list[int]) -> None:
    loops: list[int] = []

    async def call() -> str:
        loops.append(id(asyncio.get_running_loop()))
        return "reply"

    assert run_coro_blocking(call(), timeout=5.0) == "reply"
    assert drained == loops  # same loop, still open when the drain ran


def test_the_drain_runs_even_when_the_call_fails(drained: list[int]) -> None:
    async def boom() -> None:
        raise ValueError("provider said no")

    with pytest.raises(ValueError, match="provider said no"):
        run_coro_blocking(boom(), timeout=5.0)
    assert len(drained) == 1


def test_the_drain_runs_after_a_timeout(drained: list[int]) -> None:
    async def slow() -> None:
        await asyncio.sleep(5)

    with pytest.raises(TimeoutError):
        run_coro_blocking(slow(), timeout=0.1)
    assert len(drained) == 1


def test_the_calling_loop_is_drained_before_the_hop(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-083: a main-loop callback in flight across the hop raised task_done() on LiteLLM 1.86."""
    import importlib

    runner = importlib.import_module("aaa.agents.tier1.phases.agent_runner.logger")
    from aaa.platform import async_timeout

    order: list[str] = []

    async def drain() -> None:
        order.append("drain")

    def hop(coro, timeout):  # noqa: ARG001 — mirrors run_coro_blocking's signature
        order.append("hop")
        coro.close()
        return "reply"

    class _Agent:
        async def process(self, _dispatch):
            return "unused"

    monkeypatch.setattr(tracing, "drain_llm_callbacks", drain)
    monkeypatch.setattr(async_timeout, "run_coro_blocking", hop)
    assert asyncio.run(runner._invoke(_Agent(), {}, 5)) == "reply"
    assert order[:2] == ["drain", "hop"]


def test_the_worker_loop_closes_only_its_own_cached_llm_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-088: clients cached on a worker loop were later closed from the orchestrator's loop."""
    import sys
    import types

    from aaa.platform.loop_clients import close_loop_llm_clients

    closed: list[str] = []

    class _Client:
        def __init__(self, name: str) -> None:
            self.name = name

        async def close(self) -> None:
            closed.append(self.name)

    class _Cache:
        def __init__(self) -> None:
            self.cache_dict: dict = {}

        def _remove_key(self, key: str) -> None:
            self.cache_dict.pop(key, None)

    cache = _Cache()
    monkeypatch.setitem(sys.modules, "litellm", types.SimpleNamespace(in_memory_llm_clients_cache=cache))

    async def phase() -> int:
        here = id(asyncio.get_running_loop())
        cache.cache_dict.update({f"httpx_openrouter-{here}": _Client("mine"),
                                 "httpx_openrouter-12345": _Client("other loop")})
        return await close_loop_llm_clients()

    assert asyncio.run(phase()) == 1
    assert closed == ["mine"] and list(cache.cache_dict) == ["httpx_openrouter-12345"]


def test_the_worker_loop_closes_every_session_bound_to_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-093: an uncached LiteLLM handler's session outlived its loop and was closed from another."""
    import sys
    import types

    from aaa.platform.loop_clients import close_loop_sessions

    class _Session:
        def __init__(self, loop) -> None:
            self._loop, self.closed = loop, False

        async def close(self) -> None:
            self.closed = True

    class LiteLLMAiohttpTransport:  # the type the sweep looks for
        def __init__(self, session) -> None:
            self.client = session

    module = types.ModuleType("litellm.llms.custom_httpx.aiohttp_transport")
    setattr(module, "LiteLLMAiohttpTransport", LiteLLMAiohttpTransport)
    monkeypatch.setitem(sys.modules, "litellm.llms.custom_httpx.aiohttp_transport", module)

    async def phase():
        mine = LiteLLMAiohttpTransport(_Session(asyncio.get_running_loop()))
        other = LiteLLMAiohttpTransport(_Session(object()))
        return await close_loop_sessions(), mine, other

    closed, mine, other = asyncio.run(phase())
    assert closed == 1 and mine.client.closed and not other.client.closed
