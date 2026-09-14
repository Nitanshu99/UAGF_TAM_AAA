"""Applying human decisions to the deferred-HITL review packet."""
from __future__ import annotations

from aaa.tools.hitl_review import apply_human_decisions, build_hitl_review_packet
from tests.unit.support.hitl_state import hitl_state


def test_accept_decision_admits_and_clears_hitl():
    state = hitl_state()
    packet = build_hitl_review_packet(state)
    for c in packet["cases"]:
        c["human_decision"] = "accept"
        c["reviewed_by"] = "auditor@x"
    summary = apply_human_decisions(state, packet)
    assert summary["resolved"] == 2 and summary["still_hitl"] is False
    assert state["hitl_required"] is False
    crit = state["verifier_critiques"]
    assert crit["T06_datasheet_for_datasets"]["verdict"] == "accept_with_notes"
    assert crit["T09_model_card"]["human_reviewed"] is True


def test_uphold_and_blank_leave_case_unresolved():
    state = hitl_state()
    packet = build_hitl_review_packet(state)
    cases = {c["template_id"]: c for c in packet["cases"]}
    cases["T06_datasheet_for_datasets"]["human_decision"] = "uphold_escalation"
    # T09 left blank
    summary = apply_human_decisions(state, packet)
    assert summary["resolved"] == 0 and summary["unresolved"] == 2
    assert state["hitl_required"] is True  # still gated


def test_override_sets_explicit_verdict():
    state = hitl_state()
    packet = build_hitl_review_packet(state)
    c = next(c for c in packet["cases"] if c["template_id"] == "T09_model_card")
    c["human_decision"] = "override"
    c["human_suggested_verdict"] = "accept"
    other = next(c for c in packet["cases"]
                 if c["template_id"] == "T06_datasheet_for_datasets")
    other["human_decision"] = "accept"
    apply_human_decisions(state, packet)
    assert state["verifier_critiques"]["T09_model_card"]["verdict"] == "accept"
