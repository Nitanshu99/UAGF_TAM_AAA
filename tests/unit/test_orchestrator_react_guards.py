"""Hard gates applied around Orchestrator ReAct decisions."""
from __future__ import annotations

from aaa.agents.tier1.orchestrator.react import Decision
from aaa.agents.tier1.orchestrator.react.guards import _PHASE_CAP, apply_guards


def test_guard_art5_halt_overrides_any_dispatch():
    """A prohibited risk tier forces FINALIZE with an audit note."""
    decision = Decision(action="DISPATCH", phase_id="P2")
    out, note = apply_guards(decision, {"risk_tier": "prohibited"}, [])
    assert out.action == "FINALIZE"
    assert note is not None and "Art.5" in note


def test_guard_intake_gate_blocks_phase_1():
    """intake_completeness_score below 0.80 blocks a P1 dispatch."""
    decision = Decision(action="DISPATCH", phase_id="P1")
    out, note = apply_guards(decision, {"intake_completeness_score": 0.5}, [])
    assert out.action == "FINALIZE"
    assert note is not None and "0.5" in note


def test_guard_dispatch_cap_redirects_to_matrix():
    """A phase dispatched past the rerun cap is redirected to ASSEMBLE_MATRIX."""
    history = [{"action": "DISPATCH", "phase_id": "P3"}] * _PHASE_CAP
    out, note = apply_guards(Decision(action="DISPATCH", phase_id="P3"), {}, history)
    assert out.action == "ASSEMBLE_MATRIX"
    assert note is not None


def test_guard_finalize_requires_matrix():
    """FINALIZE without a compliance matrix is corrected to ASSEMBLE_MATRIX."""
    out, note = apply_guards(Decision(action="FINALIZE"), {}, [])
    assert out.action == "ASSEMBLE_MATRIX"
    assert note is not None


def test_guard_passes_compliant_decision_through():
    """A compliant decision is returned unchanged with no note."""
    state = {"intake_completeness_score": 1.0, "compliance_matrix": {"Art.5": "PASS"}}
    decision = Decision(action="FINALIZE", rationale="all phases admitted")
    out, note = apply_guards(decision, state, [])
    assert out is decision
    assert note is None


def test_phase_id_variants_normalise():
    """Loose model phrasings map onto the canonical phase ids."""
    from aaa.agents.tier1.orchestrator.react.decisions import normalise_phase
    assert normalise_phase("P4_Output") == "P4"
    assert normalise_phase("Phase 2") == "P2"
    assert normalise_phase("p3") == "P3"
    assert normalise_phase("CYBER") == "CYBER"


def test_guard_blocks_close_while_mandatory_phase_unrun():
    """ASSEMBLE_MATRIX/FINALIZE is redirected to the phase that never ran."""
    state = {"phase_plan": {"P1": "M", "P4": "M"},
             "phase_artefacts": {"T02_system_card": {}},
             "compliance_matrix": {"Art.5": "PASS"}}
    for action in ("ASSEMBLE_MATRIX", "FINALIZE"):
        out, note = apply_guards(Decision(action=action), state, [])
        assert out.action == "DISPATCH" and out.phase_id == "P4"
        assert note is not None and "overstate conformity" in note


def test_guard_allows_close_once_mandatory_phases_ran():
    """With every mandatory artefact present the decision passes through."""
    state = {"phase_plan": {"P1": "M", "P4": "M"},
             "phase_artefacts": {"T02_system_card": {},
                                 "T12_output_fairness_report": {}},
             "compliance_matrix": {"Art.5": "PASS"}}
    decision = Decision(action="FINALIZE")
    out, note = apply_guards(decision, state, [])
    assert out is decision and note is None
