"""HITL packet coverage when the verdict, not the Verifier, demands review."""
from __future__ import annotations

from aaa.tools.hitl_review import build_hitl_review_packet, hitl_cases
from aaa.tools.hitl_review.verdict.cases import verdict_case_findings
from tests.unit.support.hitl_verdict_state import state


def test_no_verifier_escalation_still_yields_cases():
    """The regression: hitl_required with zero escalations produced no packet."""
    audit_state = state()
    assert hitl_cases(audit_state) == []          # nothing escalated
    packet = build_hitl_review_packet(audit_state)
    assert packet["hitl_required"] is True
    assert len(packet["cases"]) == 1
    case = packet["cases"][0]
    assert case["template_id"] == "T12_output_fairness_report"
    assert case["escalation_source"] == "verdict"
    assert case["verdict"] is None
    assert "P4-FAIR-AGE_GROUP" in case["issues"][0]
    assert case["article_citations"] == ["Art.10§2(f)", "Art.15§1"]
    assert case["artefact_uri"] == "minio://eng-t/T12.json"


def test_verdict_cases_ignore_observations():
    """Only material / possibly-material findings become review cases."""
    grouped = verdict_case_findings(state())
    assert set(grouped) == {"T12_output_fairness_report"}
    assert len(grouped["T12_output_fairness_report"]) == 1
