"""Deferred-HITL review packet construction."""
from __future__ import annotations

from aaa.tools.hitl_review import build_hitl_review_packet, hitl_cases
from tests.unit.support.hitl_state import hitl_state


def test_hitl_cases_lists_only_escalated():
    assert set(hitl_cases(hitl_state())) == {"T06_datasheet_for_datasets",
                                             "T09_model_card"}


def test_build_packet_has_cases_evidence_and_empty_human_fields():
    packet = build_hitl_review_packet(hitl_state())
    assert packet["status"] == "PENDING_HUMAN_REVIEW"
    assert len(packet["cases"]) == 2
    case = next(c for c in packet["cases"]
                if c["template_id"] == "T06_datasheet_for_datasets")
    assert case["phase"] == "P2 Data Governance"
    assert case["issues"]                      # why it escalated
    assert "minio://e/p2/T06.json" in case["evidence_uris"]   # fetched evidence
    # Human input fields are present and empty, ready to fill.
    assert case["human_decision"] == "" and case["human_rationale"] == ""
    assert case["reviewed_by"] == ""
