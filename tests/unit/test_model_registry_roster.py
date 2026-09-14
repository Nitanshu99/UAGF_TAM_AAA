"""Roster integrity and model-assignment snapshot for model_registry.

Pins the GPT-5.6 agent → (model, service_tier) assignment so any silent
edit to AGENT_MODELS surfaces as a test failure in PR review.
"""
from __future__ import annotations

import pytest

from aaa.platform.model_registry import AGENT_MODELS, FLEX_AGENTS

_EXPECTED_AGENTS = {
    "Orchestrator", "Verifier", "Regulatory RAG", "ScopeAgent", "DataAuditor",
    "ModelValidator", "OutputFairnessTester", "GovernanceAgent", "ReportArchitect",
    "UAGF-TAM-L", "CyberSecurityAgent", "PrivacyDPOAgent",
    "DocIntelligenceAgent",  # added in extended roster
    "ClientBrief",  # writes the customer-facing brief after Phase 6
}


def test_registry_contains_all_agents():
    """All registered agents must be present in AGENT_MODELS."""
    assert set(AGENT_MODELS.keys()) == _EXPECTED_AGENTS
    assert len(AGENT_MODELS) == len(_EXPECTED_AGENTS)


def test_flex_agents_set_is_empty_after_gpt56_migration():
    """Sol/Terra reject the Flex tier, so no agent is registered for it."""
    assert FLEX_AGENTS == frozenset()


def test_no_agent_carries_a_service_tier():
    """GPT-5.6 migration: every agent ships without a service_tier."""
    for name, cfg in AGENT_MODELS.items():
        assert cfg.service_tier is None, f"{name} must stay on default tier (not flex)"


@pytest.mark.parametrize("agent,expected_model", [
    ("Orchestrator", "gpt-5.6-sol"),
    ("Verifier", "gpt-5.6-terra"),
    ("Regulatory RAG", "gpt-5.6-luna"),
    ("ScopeAgent", "gpt-5.6-terra"),
    ("DataAuditor", "gpt-5.6-terra"),
    ("ModelValidator", "gpt-5.6-terra"),
    ("OutputFairnessTester", "gpt-5.6-luna"),
    ("GovernanceAgent", "gpt-5.6-terra"),
    ("ReportArchitect", "gpt-5.6-terra"),
    ("UAGF-TAM-L", "gpt-5.6-terra"),
    ("CyberSecurityAgent", "gpt-5.6-terra"),
    ("PrivacyDPOAgent", "gpt-5.6-terra"),
    ("DocIntelligenceAgent", "gpt-5.6-terra"),
])
def test_model_assignment_snapshot(agent, expected_model):
    """Each agent resolves to its agreed GPT-5.6 family model."""
    assert AGENT_MODELS[agent].model == expected_model
