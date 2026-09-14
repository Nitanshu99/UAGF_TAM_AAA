"""An escalation on a field the template does not define does not block admission (T-20260914-053)."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.unfounded import downgrade_unfounded_escalation


def _state(tid: str, field: str, accuracy: int = 2) -> dict:
    issue = {"issue_type": "artefact_defect", "materiality": "material", "severity": "major",
             "field": field, "description": "missing"}
    return {"verifier_critiques": {tid: {"verdict": "escalate_hitl", "issues": [issue],
                                         "scores": {"factual_accuracy": accuracy}}}}


def test_t10_evidence_uris_escalation_is_admitted_with_a_note() -> None:
    """Case 01 x1a1: T10 defines no evidence_uris."""
    state = _state("T10_explainability_report", "evidence_uris")
    verdict = downgrade_unfounded_escalation(state, "T10_explainability_report",
                                             "escalate_hitl", "Phase 3")
    assert verdict == "accept_with_notes"
    assert "does not define (evidence_uris)" in state["verifier_critiques"][
        "T10_explainability_report"]["notes"][0]


def test_a_contracted_field_or_a_factual_failure_keeps_the_escalation() -> None:
    """dataset_summary is a T07 property; factual_accuracy 0 is never downgraded."""
    tid = "T07_data_quality_report"
    assert downgrade_unfounded_escalation(_state(tid, "dataset_summary.num_rows"), tid,
                                          "escalate_hitl", "Phase 2") == "escalate_hitl"
    t10 = "T10_explainability_report"
    assert downgrade_unfounded_escalation(_state(t10, "evidence_uris", accuracy=0), t10,
                                          "escalate_hitl", "Phase 3") == "escalate_hitl"
