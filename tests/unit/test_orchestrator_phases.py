"""Tests for extracted orchestrator phase modules."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# initial_state
# ---------------------------------------------------------------------------

def test_build_initial_state_defaults():
    from aaa.agents.tier1.phases.initial_state import build_initial_state

    state = build_initial_state("eng-001", {"stage_a": {"declared_modality": "tabular"}})
    assert state["engagement_id"] == "eng-001"
    assert state["declared_modality"] == "tabular"
    assert state["final_verdict"] is None
    assert state["phase_artefacts"] == {}
    assert state["hitl_required"] is False


def test_build_initial_state_llm_modality():
    from aaa.agents.tier1.phases.initial_state import build_initial_state

    state = build_initial_state("eng-llm", {"stage_a": {"declared_modality": "llm"}})
    assert state["is_llm_or_agentic"] is True


# ---------------------------------------------------------------------------
# node_stage0
# ---------------------------------------------------------------------------

def test_node_stage0_passes_high_score():
    from aaa.agents.tier1.phases.node_stage0 import node_stage0

    state = {"engagement_id": "x", "intake_completeness_score": 0.95, "hitl_required": False}
    result = node_stage0(state)
    assert result["hitl_required"] is False


def test_node_stage0_blocks_low_score():
    from aaa.agents.tier1.phases.node_stage0 import node_stage0

    state = {"engagement_id": "x", "intake_completeness_score": 0.50, "hitl_required": False}
    result = node_stage0(state)
    assert result["hitl_required"] is True
    assert "0.50" in result["hitl_reason"]


# ---------------------------------------------------------------------------
# node_route
# ---------------------------------------------------------------------------

def test_node_route_standard():
    from aaa.agents.tier1.phases.node_stubs import node_route

    state = {"engagement_id": "x", "is_llm_or_agentic": False}
    result = node_route(state)
    assert result["_branch"] == "standard"


def test_node_route_l_branch():
    from aaa.agents.tier1.phases.node_stubs import node_route

    state = {"engagement_id": "x", "is_llm_or_agentic": True}
    result = node_route(state)
    assert result["_branch"] == "l_branch"


# ---------------------------------------------------------------------------
# node_phase1_stub
# ---------------------------------------------------------------------------

def test_node_phase1_stub_fills_artefacts():
    from aaa.agents.tier1.phases.node_stubs import node_phase1_stub

    state = {
        "engagement_id": "eng-001",
        "phase_artefacts": {},
        "verifier_critiques": {},
    }
    result = node_phase1_stub(state)
    assert "T02_system_card" in result["phase_artefacts"]
    assert "T05_art43_decision" in result["verifier_critiques"]


# ---------------------------------------------------------------------------
# compliance_matrix
# ---------------------------------------------------------------------------

def test_node_compliance_matrix_pass_verdict():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    state = {
        "engagement_id": "eng-cm",
        "intake_completeness_score": 0.95,
        "completeness_score": None,
        "regulatory_coverage_pct": None,
        "scope_gate": {},
        "verifier_critiques": {
            "T02_system_card": {"verdict": "accept", "article_citations": ["Art.5"]},
            "T03_annex_iii_mapping": {"verdict": "accept", "article_citations": ["Art.6"]},
        },
        "phase_artefacts": {},
        "compliance_matrix": {},
        "blocking_findings": [],
        "cgsa_phase5_verdict": None,
        "cgsa_csp_satisfiable": True,
        "annex_iii_mapping": [],
        "harmonised_standards_applied": False,
        "risk_tier": "minimal",
        "provider_elects_third_party": False,
    }
    result = node_compliance_matrix(state)
    assert result["final_verdict"] in {"PASS", "PASS_WITH_OBSERVATIONS", "FAIL"}
    assert "Art.5" in result["compliance_matrix"]


# ---------------------------------------------------------------------------
# checkpointer
# ---------------------------------------------------------------------------

def test_in_memory_checkpointer():
    from aaa.agents.tier1.checkpointer import make_checkpointer

    cp = make_checkpointer()
    cp.put("t1", {"a": 1})
    assert cp.get("t1") == {"a": 1}
    assert cp.get("missing") is None
