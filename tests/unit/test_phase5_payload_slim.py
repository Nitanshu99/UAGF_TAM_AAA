"""The Phase 5 prompt must not carry the same finding twice (M6).

``aaa_phase5_handoff`` and ``ingest_state_delta`` both carry the blocking
findings, the low-confidence controls, the positive findings, the follow-up list
and the narrative. The delta's copies are strict supersets — each finding joined
to its control name, remediation action and full article list — so the raw ones
are read first and answer less.
"""
from __future__ import annotations

import json

from aaa.agents.tier2.governance_agent.payload_slim import _RESTATED, slim_cgsa_payload

_PAYLOAD = {
    "schema_version": "1.0",
    "domains": [{"domain_id": "D3", "controls": [{"control_id": "C15"}]}],
    "remediation_roadmap": [{"control_id": "C02", "control_name": "Legal gate",
                             "eu_ai_act_article": "Article 9", "current_score": 2}],
    "aaa_phase5_handoff": {
        "assessment_id": "a-1",
        "annex_iv_completeness": 0.8,
        "critical_gaps": 3,
        "s5_integration_note": "keep me",
        "blocking_findings": [{"control_id": "C02", "severity": "critical"}],
        "low_confidence_controls": [{"control_id": "C07"}],
        "positive_findings": [],
        "aaa_recommended_follow_up": ["do the thing"],
        "phase5_narrative_summary": "a summary",
    },
}


def test_the_restated_fields_are_dropped():
    handoff = slim_cgsa_payload(_PAYLOAD)["aaa_phase5_handoff"]
    for key in _RESTATED:
        assert key not in handoff


def test_everything_not_restated_is_kept():
    """Dropping a field nothing else carries would be a worse defect."""
    handoff = slim_cgsa_payload(_PAYLOAD)["aaa_phase5_handoff"]
    for key in ("assessment_id", "annex_iv_completeness", "critical_gaps",
                "s5_integration_note"):
        assert handoff[key] == _PAYLOAD["aaa_phase5_handoff"][key]


def test_the_remediation_roadmap_is_untouched():
    """The delta's normalisation of it is lossy, so the raw one is not a copy."""
    assert slim_cgsa_payload(_PAYLOAD)["remediation_roadmap"] == \
        _PAYLOAD["remediation_roadmap"]


def test_the_controls_are_untouched():
    """The 38-control detail is what T14/T15 are written from."""
    assert slim_cgsa_payload(_PAYLOAD)["domains"] == _PAYLOAD["domains"]


def test_the_model_is_told_where_they_went():
    handoff = slim_cgsa_payload(_PAYLOAD)["aaa_phase5_handoff"]
    assert "ingest_state_delta" in handoff["_moved"]
    assert "blocking_findings" in handoff["_moved"]


def test_the_input_is_not_mutated():
    """The state's copy of the payload must survive intact."""
    before = json.dumps(_PAYLOAD, sort_keys=True)
    slim_cgsa_payload(_PAYLOAD)
    assert json.dumps(_PAYLOAD, sort_keys=True) == before


def test_a_payload_without_a_handoff_is_returned_unchanged():
    assert slim_cgsa_payload({"domains": []}) == {"domains": []}
    assert slim_cgsa_payload(None) is None


def test_it_actually_gets_smaller_at_real_scale():
    """Call #052 carried 32 blocking findings and 24 low-confidence controls."""
    payload = json.loads(json.dumps(_PAYLOAD))
    payload["aaa_phase5_handoff"]["blocking_findings"] = [
        {"control_id": f"C{i:02d}", "finding_type": "hard_constraint_violation",
         "severity": "critical",
         "description": f"Hard constraint violated for control C{i:02d}."}
        for i in range(32)]
    payload["aaa_phase5_handoff"]["low_confidence_controls"] = [
        {"control_id": f"C{i:02d}", "confidence": 0.4} for i in range(24)]

    before = len(json.dumps(payload))
    after = len(json.dumps(slim_cgsa_payload(payload)))
    assert after < before
    # The pointer costs a few hundred characters; the saving is thousands.
    assert before - after > 4000
