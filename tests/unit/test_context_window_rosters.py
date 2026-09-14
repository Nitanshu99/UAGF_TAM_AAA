"""Declared context windows must resolve from every roster, not just OpenAI's."""
from __future__ import annotations

from aaa.platform.model_registry.nvidia_roster import NVIDIA_AGENT_MODELS
from aaa.platform.model_registry.roster import AGENT_MODELS
from aaa.platform.token_guard.get_context_window.window import get_context_window
from aaa.platform.token_guard.logger import _FALLBACK_CONTEXT_WINDOW


def test_nvidia_declared_window_is_found() -> None:
    """A window declared on a NIM config must not fall back.

    ``_declared_window`` searched only ``AGENT_MODELS``, so every
    ``nvidia_nim/*`` id — the ones this field exists for, since none appear in
    LiteLLM's cost map — silently used the generic window and left the token
    guard disarmed.
    """
    config = NVIDIA_AGENT_MODELS["Orchestrator"]
    assert config.context_window, "the NIM roster must declare a context window"
    assert get_context_window(config.model) == config.context_window
    assert get_context_window(config.model) != _FALLBACK_CONTEXT_WINDOW


def test_openai_roster_still_resolves() -> None:
    """Adding the NIM roster must not shadow the OpenAI one."""
    model = AGENT_MODELS["Verifier"].model
    assert get_context_window(model) > _FALLBACK_CONTEXT_WINDOW


def test_unknown_model_falls_back() -> None:
    """An unlisted model still gets the generic window, loudly."""
    assert get_context_window("no-such-provider/no-such-model") == _FALLBACK_CONTEXT_WINDOW
