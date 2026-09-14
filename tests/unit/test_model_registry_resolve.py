"""ModelConfig helpers and the model/service-tier resolvers."""
from __future__ import annotations

import pytest

from aaa.platform.model_registry import (
    ModelConfig,
    get_model_config,
    resolve_model,
    resolve_service_tier,
)


@pytest.fixture(autouse=True)
def _openai_provider(monkeypatch):
    """Pin every test in this file to the OpenAI roster.

    ``get_model_config``/``resolve_model`` now read ``PROVIDER`` from the
    real environment (see ``resolve._active_roster``); without this,
    a developer's local ``.env`` (e.g. ``PROVIDER=nvidia``) would silently
    flip these GPT-5.6 snapshot assertions.
    """
    monkeypatch.delenv("PROVIDER", raising=False)


def test_litellm_kwargs_omits_service_tier_when_unset():
    """litellm_kwargs carries only the model when no tier is set."""
    assert ModelConfig(model="gpt-5.6-terra").litellm_kwargs() == {"model": "gpt-5.6-terra"}


def test_litellm_kwargs_includes_service_tier_when_flex():
    """litellm_kwargs forwards an explicitly set service tier."""
    # Dataclass behaviour: a tier set explicitly (e.g. Luna flex override)
    # is forwarded to litellm even though no registry entry ships one.
    cfg = ModelConfig(model="gpt-5.6-luna", service_tier="flex")
    assert cfg.litellm_kwargs() == {"model": "gpt-5.6-luna", "service_tier": "flex"}


def test_model_config_is_immutable():
    """ModelConfig is frozen; attribute assignment raises."""
    cfg = ModelConfig(model="gpt-5.6-terra")
    with pytest.raises(Exception):  # FrozenInstanceError subclasses AttributeError
        cfg.model = "other"  # type: ignore[misc]


def test_get_model_config_returns_registered_entry():
    """get_model_config returns the registered GPT-5.6 entry."""
    cfg = get_model_config("Verifier")
    assert cfg.model == "gpt-5.6-terra"
    assert cfg.service_tier is None


def test_get_model_config_raises_on_unknown():
    """Unknown agent names raise KeyError at construction time."""
    with pytest.raises(KeyError):
        get_model_config("NotAnAgent")


def test_resolve_model_returns_override_when_given():
    """resolve_model prefers a non-empty override."""
    assert resolve_model("Verifier", "custom-model") == "custom-model"


def test_resolve_model_returns_registry_default_when_no_override():
    """resolve_model falls back to the registry default."""
    assert resolve_model("Verifier", None) == "gpt-5.6-terra"


def test_resolve_service_tier_returns_override_when_given(monkeypatch):
    """resolve_service_tier applies an explicit override."""
    # Explicit override is applied when not None.
    monkeypatch.delenv("AAA_DISABLE_FLEX", raising=False)
    assert resolve_service_tier("Verifier", "default") == "default"


def test_resolve_service_tier_returns_registry_default(monkeypatch):
    """Registry default tier is None for every migrated agent."""
    # Post-migration registry default is None for every agent.
    monkeypatch.delenv("AAA_DISABLE_FLEX", raising=False)
    assert resolve_service_tier("Verifier", None) is None
    assert resolve_service_tier("Orchestrator", None) is None


def test_resolve_service_tier_disabled_via_env(monkeypatch):
    """AAA_DISABLE_FLEX suppresses any service tier."""
    # AAA_DISABLE_FLEX=true forces no service_tier for backends without Flex.
    monkeypatch.setenv("AAA_DISABLE_FLEX", "true")
    assert resolve_service_tier("Verifier", None) is None
    assert resolve_service_tier("Verifier", "default") is None
