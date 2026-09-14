"""PROVIDER=openrouter routes the roster and throttles at the free-tier cap."""
from __future__ import annotations

import asyncio

import pytest

from aaa.platform.model_registry.openrouter.roster import OPENROUTER_AGENT_MODELS
from aaa.platform.model_registry.provider import OPENROUTER, active_provider
from aaa.platform.model_registry.resolve import resolve_model
from aaa.platform.rate_limit import (
    MAX_REQUESTS_PER_WINDOW,
    OPENROUTER_REQUESTS_PER_WINDOW,
    FixedWindowLimiter,
)


def test_env_selects_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    """The switch recognises the third provider."""
    monkeypatch.setenv("PROVIDER", "openrouter")
    assert active_provider() == OPENROUTER


def test_nvidia_remains_the_configured_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adding OpenRouter must not change what an unset PROVIDER resolves to."""
    monkeypatch.delenv("PROVIDER", raising=False)
    assert active_provider() == "openai"
    monkeypatch.setenv("PROVIDER", "nvidia")
    assert resolve_model("Verifier", None).startswith("nvidia_nim/")


def test_roster_dispatches_to_the_free_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every agent resolves to the ``:free`` OpenRouter slug."""
    monkeypatch.setenv("PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    assert resolve_model("Orchestrator", None) == (
        "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free")
    # Compared against the primary roster, not a literal: a mirror that is one
    # agent short falls back to OpenAI for that agent under PROVIDER=openrouter,
    # and a hard-coded count only catches it if someone remembers to bump it.
    from aaa.platform.model_registry import AGENT_MODELS
    assert set(OPENROUTER_AGENT_MODELS) == set(AGENT_MODELS)
    assert {c.model for c in OPENROUTER_AGENT_MODELS.values()} == {
        "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"}


def test_free_route_declares_its_context_window() -> None:
    """The ``:free`` route publishes 1M, unlike the paid variant's 512288."""
    assert OPENROUTER_AGENT_MODELS["Verifier"].context_window == 1_000_000


def test_override_still_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit override beats the active provider's registry."""
    monkeypatch.setenv("PROVIDER", "openrouter")
    assert resolve_model("Verifier", "custom-model") == "custom-model"


def test_openrouter_cap_is_lower_than_nim() -> None:
    """OpenRouter allows 20/min on free routes; NIM allows 40."""
    assert OPENROUTER_REQUESTS_PER_WINDOW == 20
    assert MAX_REQUESTS_PER_WINDOW == 40


def test_limiter_blocks_at_the_openrouter_cap() -> None:
    """The 20th request in a window waits for the window to roll over."""
    now = [0.0]
    limiter = FixedWindowLimiter(max_requests=OPENROUTER_REQUESTS_PER_WINDOW,
                                 window_seconds=60.0, clock=lambda: now[0])

    async def drive() -> None:
        for _ in range(OPENROUTER_REQUESTS_PER_WINDOW - 1):
            await asyncio.wait_for(limiter.acquire(), timeout=1)
        # The capped call sleeps out the remaining window rather than passing.
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(limiter.acquire(), timeout=0.05)

    asyncio.run(drive())
