"""Unit tests for the Langfuse LiteLLM tracing seam (configure_llm_tracing)."""
from __future__ import annotations

import sys
import types

import pytest

from aaa.observability import tracing


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    """Reset the idempotency latch and stub litellm around every test."""
    tracing.reset_llm_tracing_state()
    stub = types.SimpleNamespace(success_callback=[], failure_callback=[])
    monkeypatch.setitem(sys.modules, "litellm", stub)
    yield
    tracing.reset_llm_tracing_state()


def test_noop_when_credentials_missing(monkeypatch):
    """Without both keys, tracing stays off and litellm is left untouched."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "langfuse_public_key", "")
    monkeypatch.setattr(settings, "langfuse_secret_key", "")
    assert tracing.configure_llm_tracing() is False
    assert sys.modules["litellm"].success_callback == []


def test_registers_callback_when_configured(monkeypatch):
    """Both keys present → litellm gets the langfuse success/failure callback."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    assert tracing.configure_llm_tracing() is True
    assert tracing._CALLBACK in sys.modules["litellm"].success_callback
    assert tracing._CALLBACK in sys.modules["litellm"].failure_callback


def test_callback_targets_the_otel_langfuse_sdk():
    """The v4 SDK dropped langfuse.version, which the legacy callback reads."""
    assert tracing._CALLBACK == "langfuse_otel"


def test_idempotent_second_call_does_not_duplicate(monkeypatch):
    """Calling twice never appends the callback to the list twice."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    tracing.configure_llm_tracing()
    tracing.configure_llm_tracing()
    assert sys.modules["litellm"].success_callback.count(tracing._CALLBACK) == 1
