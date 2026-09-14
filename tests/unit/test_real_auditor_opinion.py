"""The auditor-opinion ladder including the disclaimer of opinion."""
from __future__ import annotations

from aaa.agents.tier2.report_architect import _auditor_opinion


def test_opinion_disclaimer_when_core_insufficient():
    decl = {
        "compliance_matrix": {"Art.15": "INSUFFICIENT_EVIDENCE"},
        "opinion_disclaimer": True, "material_findings_count": 0,
        "blocking_findings": [], "stage_a": {"system_name": "CreditGuard"},
    }
    op = _auditor_opinion(decl, "PASS_WITH_OBSERVATIONS")
    assert op["opinion_type"] == "disclaimer_of_opinion"
    assert "Art.15" in op["basis_paragraph"]


def test_opinion_adverse_on_fail():
    decl = {"compliance_matrix": {"Art.15": "FAIL"}, "blocking_findings": [],
            "stage_a": {"system_name": "S"}}
    assert _auditor_opinion(decl, "FAIL")["opinion_type"] == "adverse"


def test_opinion_unqualified_clean_pass():
    decl = {"compliance_matrix": {"Art.15": "PASS"}, "material_findings_count": 0,
            "blocking_findings": [], "stage_a": {"system_name": "S"}}
    assert _auditor_opinion(decl, "PASS")["opinion_type"] == "unqualified"
