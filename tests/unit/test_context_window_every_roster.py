"""The guard must read the declared window from whichever roster declares it.

``_declared_window`` says it searches *every* roster. It searched two. The
OpenRouter roster was added afterwards and never wired in, so for every
``openrouter/*`` id — the default provider since 2026-09-09 — the declared
window was ignored and LiteLLM's cost map won.

That is worse on OpenRouter than anywhere else, because it fronts many endpoints
per model and the map answers for the *model*. Pinned to CoreWeave, which serves
262,144 tokens, the guard sized budgets against the 1,048,576 the map reports
for ``minimax/minimax-m3``: four times what the endpoint accepts, and permissive,
which is the direction that does not fail loudly.
"""
from __future__ import annotations

import pytest

from aaa.platform.model_registry.model_config import ModelConfig
from aaa.platform.token_guard import get_context_window


@pytest.fixture
def _pinned(monkeypatch):
    """Resolve the OpenRouter roster with MiniMax pinned to CoreWeave."""
    monkeypatch.setenv("PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_MODEL", "minimax/minimax-m3")
    monkeypatch.setenv("OPENROUTER_PROVIDER", "coreweave/fp4")
    import importlib

    import aaa.platform.model_registry.openrouter.roster as roster
    importlib.reload(roster)
    yield roster
    for name in ("OPENROUTER_MODEL", "OPENROUTER_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    importlib.reload(roster)


def test_a_pinned_endpoints_window_reaches_the_guard(_pinned):
    """The acceptance criterion, stated as an assertion."""
    config = _pinned.OPENROUTER_AGENT_MODELS["Verifier"]
    assert config.context_window == 262_144
    assert get_context_window(config.model) == 262_144, (
        "the guard fell back to LiteLLM's per-model window and would permit "
        "prompts this endpoint cannot accept")


def test_every_roster_is_consulted():
    """Structural: a roster added later must be added here too."""
    import inspect

    from aaa.platform.token_guard.get_context_window import window
    src = inspect.getsource(window._declared_window)
    for roster in ("AGENT_MODELS", "NVIDIA_AGENT_MODELS", "OPENROUTER_AGENT_MODELS"):
        assert roster in src, f"{roster} is not consulted"


def test_an_undeclared_model_still_falls_through():
    """The fallback chain is unchanged for ids no roster declares."""
    assert get_context_window("some/model-nobody-declared") > 0


def test_a_declared_window_beats_the_cost_map(monkeypatch):
    """Priority order: the roster's figure is the endpoint's, and it wins."""
    from aaa.platform.token_guard.get_context_window import window
    fake = {"Verifier": ModelConfig("openrouter/fake/model", context_window=1234)}
    monkeypatch.setattr(
        "aaa.platform.model_registry.openrouter.roster.OPENROUTER_AGENT_MODELS",
        fake, raising=False)
    assert window._declared_window("openrouter/fake/model") == 1234
