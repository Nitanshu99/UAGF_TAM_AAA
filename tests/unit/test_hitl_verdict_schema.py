"""HITL packet schema stability and Verifier-escalation precedence."""
from __future__ import annotations

from aaa.tools.hitl_review import build_hitl_review_packet
from tests.unit.support.hitl_verdict_state import OBSERVATION, state


def test_case_schema_matches_the_escalation_driven_shape():
    """finalize_hitl reads these fields, so the shape must not drift."""
    case = build_hitl_review_packet(state())["cases"][0]
    for field in ("template_id", "phase", "verdict", "artefact_uri", "issues",
                  "article_citations", "scores", "total_score", "evidence_uris",
                  "human_decision", "human_suggested_verdict", "human_rationale",
                  "human_evidence_uris", "reviewed_by", "reviewed_at"):
        assert field in case, field


def test_verifier_escalation_still_takes_precedence():
    """When the Verifier did escalate, those cases are used unchanged."""
    audit_state = state(verifier_critiques={
        "T18_audit_report": {"verdict": "escalate_hitl", "issues": ["unsupported opinion"]}})
    packet = build_hitl_review_packet(audit_state)
    assert [c["template_id"] for c in packet["cases"]] == ["T18_audit_report"]
    assert "escalation_source" not in packet["cases"][0]


def test_no_packet_cases_when_review_not_required():
    """A clean engagement produces no cases at all."""
    audit_state = state(hitl_required=False, findings=[OBSERVATION])
    assert build_hitl_review_packet(audit_state)["cases"] == []
