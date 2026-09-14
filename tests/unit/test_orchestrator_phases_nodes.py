"""Tests for the extracted orchestrator node modules."""
from __future__ import annotations


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


def test_node_stage0_passes_high_score():
    from aaa.agents.tier1.phases.nodes.stage0 import node_stage0
    state = {"engagement_id": "x", "intake_completeness_score": 0.95,
             "hitl_required": False}
    assert node_stage0(state)["hitl_required"] is False


def test_node_stage0_blocks_low_score():
    from aaa.agents.tier1.phases.nodes.stage0 import node_stage0
    state = {"engagement_id": "x", "intake_completeness_score": 0.50,
             "hitl_required": False}
    result = node_stage0(state)
    assert result["hitl_required"] is True
    assert "0.50" in result["hitl_reason"]


def test_node_route_standard():
    from aaa.agents.tier1.phases.node_stubs import node_route
    assert node_route({"engagement_id": "x",
                       "is_llm_or_agentic": False})["_branch"] == "standard"


def test_node_route_l_branch():
    from aaa.agents.tier1.phases.node_stubs import node_route
    assert node_route({"engagement_id": "x",
                       "is_llm_or_agentic": True})["_branch"] == "l_branch"


def test_node_phase1_stub_fills_artefacts():
    from aaa.agents.tier1.phases.node_stubs import node_phase1_stub
    result = node_phase1_stub({"engagement_id": "eng-001",
                               "phase_artefacts": {}, "verifier_critiques": {}})
    assert "T02_system_card" in result["phase_artefacts"]
    assert "T05_art43_decision" in result["verifier_critiques"]
