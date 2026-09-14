"""``OPENROUTER_MODEL`` must not be discarded in silence (M19).

The roster reads ``OPENROUTER_MODEL`` only on the pinned branch, so setting it
alone selects nothing. That is the design — the free route is one gated
endpoint with no model choice — but it used to be invisible: a run asked for
``minimax/minimax-m3``, was served ``nvidia/nemotron-3-ultra`` and the log held
no trace of the substitution.
"""
from __future__ import annotations

import importlib
import logging

import pytest

from aaa.platform.model_registry.openrouter import roster as openrouter_roster
from aaa.platform.model_registry.openrouter.provider import DEFAULT_MODEL


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_PROVIDER", raising=False)


def test_unset_serves_the_free_default_quietly(caplog):
    with caplog.at_level(logging.WARNING):
        config = openrouter_roster._ultra()
    assert config.model == f"openrouter/{DEFAULT_MODEL}:free"
    assert "selects nothing on its own" not in caplog.text


def test_a_model_set_alone_is_refused_out_loud(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_MODEL", "minimax/minimax-m3")
    with caplog.at_level(logging.WARNING):
        config = openrouter_roster._ultra()
    assert config.model == f"openrouter/{DEFAULT_MODEL}:free"
    assert "selects nothing on its own" in caplog.text
    assert "minimax/minimax-m3" in caplog.text
    assert "OPENROUTER_PROVIDER" in caplog.text


def test_naming_the_default_model_is_not_a_substitution(monkeypatch, caplog):
    """Asking for what you are already getting is not worth a warning."""
    monkeypatch.setenv("OPENROUTER_MODEL", DEFAULT_MODEL.upper())
    with caplog.at_level(logging.WARNING):
        openrouter_roster._ultra()
    assert "selects nothing on its own" not in caplog.text


def test_a_pinned_endpoint_selects_the_paid_slug(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "minimax/minimax-m3")
    monkeypatch.setenv("OPENROUTER_PROVIDER", "coreweave/fp4")
    config = openrouter_roster._ultra()
    assert config.model == "openrouter/minimax/minimax-m3"
    assert config.context_window == 262_144
    assert ":free" not in config.model


def test_the_roster_module_still_imports_cleanly():
    importlib.reload(openrouter_roster)
    assert openrouter_roster.OPENROUTER_AGENT_MODELS["Verifier"] is not None


def test_none_is_an_explicit_free_route(monkeypatch) -> None:
    """``OPENROUTER_PROVIDER=none`` unpins without an error (T-20260914-066)."""
    from aaa.platform.model_registry.openrouter.provider import pinned_endpoint

    monkeypatch.setenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    monkeypatch.setenv("OPENROUTER_PROVIDER", "none")
    assert pinned_endpoint() is None

