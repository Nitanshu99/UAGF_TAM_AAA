"""T-20260914-016: an admitted artefact's findings about the provider decide its articles.

Admission no longer turns on them (T-20260914-015), so without this an admitted T06
recording undocumented data collection would let Art. 10 read PASS.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import _article_verdict
from aaa.agents.tier1.phases.verification.provider_findings import record_provider_findings

_TIDS = {"T06_datasheet_for_datasets": ["Art.10"], "T09_model_card": ["Art.15"]}


def _issue(kind: str, materiality: str) -> dict:
    """One normalised Verifier issue."""
    return {"issue_type": kind, "materiality": materiality, "severity": "major",
            "description": f"{kind} ({materiality})"}


def _state(t06: list, t09: list, t09_verdict: str = "accept_with_notes") -> dict:
    """Critiques for T06 and T09."""
    return {"verifier_critiques": {
        "T06_datasheet_for_datasets": {"verdict": "accept_with_notes", "issues": t06},
        "T09_model_card": {"verdict": t09_verdict, "issues": t09}}}


def _verdict(state: dict, article: str) -> str:
    """The article's matrix verdict from what the phase recorded."""
    findings = [f for f in state.get("blocking_findings") or []
                if article in f["eu_ai_act_articles"]]
    # The article is admitted (its artefact was); only findings and insufficiency differ.
    return _article_verdict(article, findings, {article},
                            set(state.get("insufficient_evidence_articles") or []))


def test_a_material_gap_is_insufficient_and_a_material_nonconformity_fails() -> None:
    """Neither article can PASS; each takes the outcome its issue calls for."""
    state = _state([_issue("evidence_gap", "material")],
                   [_issue("provider_nonconformity", "material")])
    record_provider_findings(state, _TIDS, phase_id="P2", phase_label="Phase 2")
    assert _verdict(state, "Art.10") == "INSUFFICIENT_EVIDENCE"
    assert _verdict(state, "Art.15") == "FAIL"
    assert {f["finding_id"] for f in state["blocking_findings"]} == {"P2-VER-T06-1", "P2-VER-T09-1"}


def test_minor_provider_issues_observe_and_defects_are_not_carried() -> None:
    """Possibly material → observation; an artefact defect is the gate's, not the matrix's."""
    state = _state([_issue("evidence_gap", "possibly_material"),
                    _issue("artefact_defect", "material")], [])
    record_provider_findings(state, _TIDS, phase_id="P2", phase_label="Phase 2")
    assert _verdict(state, "Art.10") == "PASS_WITH_OBSERVATIONS"
    assert len(state["blocking_findings"]) == 1


def test_a_redispatch_without_the_issue_releases_what_it_held() -> None:
    """Rewritten, not appended: the gap record, its finding and its insufficiency go."""
    state = _state([_issue("evidence_gap", "material")], [])
    record_provider_findings(state, _TIDS, phase_id="P2", phase_label="Phase 2")
    state["verifier_critiques"]["T06_datasheet_for_datasets"]["issues"] = []
    record_provider_findings(state, _TIDS, phase_id="P2", phase_label="Phase 2")
    assert not state["blocking_findings"] and not state["evidence_gap_records"]
    assert "Art.10" not in state["insufficient_evidence_articles"]


def test_an_unadmitted_artefact_is_left_to_the_unadmitted_gate() -> None:
    """Its articles are already insufficient; nothing is double-recorded."""
    state = _state([], [_issue("provider_nonconformity", "material")], t09_verdict="escalate_hitl")
    record_provider_findings(state, _TIDS, phase_id="P3", phase_label="Phase 3")
    assert "blocking_findings" not in state
