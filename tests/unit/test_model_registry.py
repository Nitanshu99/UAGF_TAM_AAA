"""
Unit tests for aaa.platform.model_registry.

Pins the redistributed agent → (model, service_tier) assignment so that any
silent edit to AGENT_MODELS surfaces as a test failure in PR review.
"""
from __future__ import annotations

import pytest

from aaa.platform.model_registry import (
    AGENT_MODELS,
    FLEX_AGENTS,
    ModelConfig,
    get_model_config,
    resolve_model,
    resolve_service_tier,
)


# ---------------------------------------------------------------------------
# Roster integrity
# ---------------------------------------------------------------------------

_EXPECTED_AGENTS = {
    "Orchestrator",
    "Verifier",
    "Regulatory RAG",
    "ScopeAgent",
    "DataAuditor",
    "ModelValidator",
    "OutputFairnessTester",
    "GovernanceAgent",
    "ReportArchitect",
    "UAGF-TAM-L",
    "CyberSecurityAgent",
    "PrivacyDPOAgent",
}


def test_registry_contains_all_twelve_agents():
    assert set(AGENT_MODELS.keys()) == _EXPECTED_AGENTS
    assert len(AGENT_MODELS) == 12


def test_flex_agents_set_matches_non_interactive_roster():
    assert FLEX_AGENTS == frozenset({
        "Verifier",
        "ModelValidator",
        "GovernanceAgent",
        "ReportArchitect",
        "UAGF-TAM-L",
    })


def test_flex_agents_have_flex_service_tier_in_registry():
    for name in FLEX_AGENTS:
        assert AGENT_MODELS[name].service_tier == "flex", (
            f"{name} should be on Flex tier"
        )


def test_non_flex_agents_have_no_service_tier():
    for name, cfg in AGENT_MODELS.items():
        if name not in FLEX_AGENTS:
            assert cfg.service_tier is None, (
                f"{name} must stay on default tier (not flex)"
            )


# ---------------------------------------------------------------------------
# Model assignments (snapshot of the redistributed table)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent,expected_model", [
    ("Orchestrator",         "gpt-5.5"),
    ("Verifier",             "gpt-5.5"),
    ("Regulatory RAG",       "gpt-5.4-nano"),
    ("ScopeAgent",           "gpt-5.4"),
    ("DataAuditor",          "gpt-5.4"),
    ("ModelValidator",       "gpt-5.5"),
    ("OutputFairnessTester", "gpt-5.4-mini"),
    ("GovernanceAgent",      "gpt-5.5"),
    ("ReportArchitect",      "gpt-5.4"),
    ("UAGF-TAM-L",           "gpt-5.5"),
    ("CyberSecurityAgent",   "gpt-5.4"),
    ("PrivacyDPOAgent",      "gpt-5.4"),
])
def test_model_assignment_snapshot(agent, expected_model):
    assert AGENT_MODELS[agent].model == expected_model


# ---------------------------------------------------------------------------
# ModelConfig.litellm_kwargs()
# ---------------------------------------------------------------------------

def test_litellm_kwargs_omits_service_tier_when_unset():
    cfg = ModelConfig(model="gpt-5.4")
    assert cfg.litellm_kwargs() == {"model": "gpt-5.4"}


def test_litellm_kwargs_includes_service_tier_when_flex():
    cfg = ModelConfig(model="gpt-5.5", service_tier="flex")
    assert cfg.litellm_kwargs() == {"model": "gpt-5.5", "service_tier": "flex"}


def test_model_config_is_immutable():
    cfg = ModelConfig(model="gpt-5.4")
    with pytest.raises(Exception):  # FrozenInstanceError subclasses AttributeError
        cfg.model = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------

def test_get_model_config_returns_registered_entry():
    cfg = get_model_config("Verifier")
    assert cfg.model == "gpt-5.5"
    assert cfg.service_tier == "flex"


def test_get_model_config_raises_on_unknown():
    with pytest.raises(KeyError):
        get_model_config("NotAnAgent")


def test_resolve_model_returns_override_when_given():
    assert resolve_model("Verifier", "custom-model") == "custom-model"


def test_resolve_model_returns_registry_default_when_no_override():
    assert resolve_model("Verifier", None) == "gpt-5.5"


def test_resolve_service_tier_returns_override_when_given():
    # Explicit None disables Flex even for a Flex-default agent.
    # Note: override is only applied if not None; pass a sentinel to disable.
    assert resolve_service_tier("Verifier", "default") == "default"


def test_resolve_service_tier_returns_registry_default():
    assert resolve_service_tier("Verifier", None) == "flex"
    assert resolve_service_tier("Orchestrator", None) is None
