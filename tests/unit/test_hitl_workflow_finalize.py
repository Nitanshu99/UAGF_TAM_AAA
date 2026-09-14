"""Finalize recompute lifts KPIs and flips the report status to FINAL."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier2.report_architect.t17 import build_t17
from aaa.tools.hitl_review import apply_human_decisions, build_hitl_review_packet
from tests.unit.support.hitl_state import hitl_state


def test_finalize_recompute_improves_completeness_and_flips_status():
    state = hitl_state()
    node_compliance_matrix(state)            # provisional
    provisional_cs = state["completeness_score"]

    packet = build_hitl_review_packet(state)
    for c in packet["cases"]:
        c["human_decision"] = "accept"
    apply_human_decisions(state, packet)
    node_compliance_matrix(state)            # final recompute

    assert state["completeness_score"] > provisional_cs  # more artefacts admitted
    t17 = build_t17("eng-test", state, "2026-06-27T00:00:00Z")
    assert t17["report_status"] == "FINAL"
    assert t17["hitl_pending"] is False


def test_provisional_report_status_when_hitl_pending():
    state = hitl_state()
    node_compliance_matrix(state)
    t17 = build_t17("eng-test", state, "2026-06-27T00:00:00Z")
    assert t17["report_status"] == "PROVISIONAL_PENDING_HITL"
    assert t17["hitl_pending"] is True
