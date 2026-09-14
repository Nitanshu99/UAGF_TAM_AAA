"""PROVIDER env switch: active_provider, key propagation, roster dispatch."""
from __future__ import annotations

import os

from aaa.platform.model_registry import get_model_config, resolve_model
from aaa.platform.model_registry.nvidia_roster import NVIDIA_AGENT_MODELS
from aaa.platform.model_registry.provider import active_provider, ensure_nvidia_key


def test_active_provider_defaults_to_openai(monkeypatch):
    """Unset PROVIDER resolves to 'openai'."""
    monkeypatch.delenv("PROVIDER", raising=False)
    assert active_provider() == "openai"


def test_active_provider_blank_falls_back_to_openai(monkeypatch):
    """A blank PROVIDER value also falls back to 'openai'."""
    monkeypatch.setenv("PROVIDER", "  ")
    assert active_provider() == "openai"


def test_active_provider_nvidia_case_and_whitespace_insensitive(monkeypatch):
    """PROVIDER=' NVIDIA ' (any case/whitespace) selects the nvidia roster."""
    monkeypatch.setenv("PROVIDER", " NVIDIA ")
    assert active_provider() == "nvidia"


def test_ensure_nvidia_key_propagates_when_unset(monkeypatch):
    """NVIDIA_API_KEY is copied into NVIDIA_NIM_API_KEY when the latter is unset."""
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-123")
    ensure_nvidia_key()
    assert os.environ["NVIDIA_NIM_API_KEY"] == "nvapi-test-123"


def test_ensure_nvidia_key_does_not_overwrite_existing(monkeypatch):
    """An explicitly-set NVIDIA_NIM_API_KEY is left untouched."""
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "already-set")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-other")
    ensure_nvidia_key()
    assert os.environ["NVIDIA_NIM_API_KEY"] == "already-set"


def test_ensure_nvidia_key_noop_without_source(monkeypatch):
    """Neither var is set when no NVIDIA_API_KEY source exists."""
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    ensure_nvidia_key()
    assert "NVIDIA_NIM_API_KEY" not in os.environ


def test_get_model_config_dispatches_to_nvidia_roster(monkeypatch):
    """PROVIDER=nvidia routes get_model_config through NVIDIA_AGENT_MODELS."""
    monkeypatch.setenv("PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    assert get_model_config("Orchestrator") == NVIDIA_AGENT_MODELS["Orchestrator"]


def test_resolve_model_dispatches_to_nvidia_roster(monkeypatch):
    """PROVIDER=nvidia routes resolve_model through the NVIDIA roster."""
    monkeypatch.setenv("PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    # Assert against the roster, not a literal id: pinning a model name here
    # only re-breaks the suite the next time a NIM model is withdrawn, which
    # is what happened to deepseek-v4-flash (EOL 2026-08-07).
    expected = NVIDIA_AGENT_MODELS["Verifier"].model
    assert expected.startswith("nvidia_nim/")
    assert resolve_model("Verifier", None) == expected


def test_resolve_model_override_wins_under_nvidia_provider(monkeypatch):
    """An explicit override still beats the active provider's registry."""
    monkeypatch.setenv("PROVIDER", "nvidia")
    assert resolve_model("Verifier", "custom-model") == "custom-model"


def test_get_model_config_still_openai_when_provider_unset(monkeypatch):
    """No PROVIDER set keeps resolving the original GPT-5.6 roster."""
    monkeypatch.delenv("PROVIDER", raising=False)
    assert get_model_config("Verifier").model == "gpt-5.6-terra"
