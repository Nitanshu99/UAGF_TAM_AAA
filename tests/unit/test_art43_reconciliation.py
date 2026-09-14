"""T05 versus the post-Phase-5 recomputation (M11).

``T05_art43_decision`` is written in Phase 1; ``harmonised_standards_applied``
arrives with the CGSA in Phase 5. The compliance matrix recomputes the decision
from the completed state and that recomputation is what the report carries, so
the two can disagree — on an Annex III point 1 system, about whether a notified
body is required. They must not disagree silently.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.art43_restatement import (
    phase1_procedure,
    reconcile_art43,
)


def _state(procedure):
    return {"art43_decision": {"procedure": procedure, "rationale": "…"}}


def test_phase1_procedure_reads_the_decision_the_scope_agent_wrote():
    assert phase1_procedure(_state("annex_vii_notified_body")) == "annex_vii_notified_body"


def test_phase1_procedure_is_none_when_phase_1_recorded_nothing():
    assert phase1_procedure({}) is None
    assert phase1_procedure({"art43_decision": None}) is None


def test_agreement_records_nothing():
    """The common case must not add a finding."""
    state = _state("annex_vi_internal_control")
    reconcile_art43(state, "annex_vi_internal_control",
                    {"procedure": "annex_vi_internal_control"})
    assert "art43_supersedes_t05" not in state
    assert not state.get("findings")


def test_a_missing_phase_1_decision_records_nothing():
    """Nothing to reconcile against is not a disagreement."""
    state = {}
    reconcile_art43(state, None, {"procedure": "annex_vi_internal_control"})
    assert not state.get("findings")


def test_disagreement_is_recorded_as_a_material_finding():
    """The notified-body flip is the case this exists for."""
    state = _state("annex_vii_notified_body")
    reconcile_art43(state, "annex_vii_notified_body",
                    {"procedure": "annex_vi_internal_control"})

    assert state["art43_supersedes_t05"] == {
        "phase1_procedure": "annex_vii_notified_body",
        "final_procedure": "annex_vi_internal_control"}
    finding = state["findings"][0]
    assert finding["finding_id"] == "ART43-SUPERSEDED"
    assert finding["materiality"] == "material"
    assert finding["eu_ai_act_articles"] == ["Art.43"]
    assert finding["declared"] == "annex_vii_notified_body"
    assert finding["observed"] == "annex_vi_internal_control"


def test_disagreement_preserves_existing_findings():
    """The finding is appended, never written over the accumulator."""
    state = {**_state("annex_vii_notified_body"), "findings": [{"finding_id": "PRIOR"}]}
    reconcile_art43(state, "annex_vii_notified_body",
                    {"procedure": "annex_vi_internal_control"})
    assert [f["finding_id"] for f in state["findings"]] == ["PRIOR", "ART43-SUPERSEDED"]
