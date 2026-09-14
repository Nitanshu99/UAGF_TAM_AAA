"""Evidence-grounded verdict derivation: FAIL / INSUFFICIENT / PASS.

These lock in that absence of evidence never yields PASS, and that the
compliance matrix is derived from findings rather than rubber-stamped.
"""
from __future__ import annotations

from tests.unit.support.real_auditor_state import base_state


def test_material_finding_forces_fail():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = base_state(blocking_findings=[
        {"finding_id": "F1", "materiality": "material",
         "eu_ai_act_articles": ["Art.15"],
         "description": "robustness probe failed"},
    ])
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.15"] == "FAIL"
    assert state["final_verdict"] == "FAIL"


def test_insufficient_not_pass():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = base_state(insufficient_evidence_articles=["Art.15"])
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.15"] == "INSUFFICIENT_EVIDENCE"
    # Core high-risk article unverifiable → disclaimer flagged, never any pass.
    # This used to read PASS_WITH_OBSERVATIONS while opinion_disclaimer was True,
    # so the headline verdict contradicted the opinion in the same state (F11).
    assert state["opinion_disclaimer"] is True
    assert state["final_verdict"] == "DISCLAIMER_OF_OPINION"


def test_admitted_no_findings_pass():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = base_state()
    node_compliance_matrix(state)
    assert state["compliance_matrix"]["Art.10"] == "PASS"
    assert state["compliance_matrix"]["Art.13"] == "PASS"
