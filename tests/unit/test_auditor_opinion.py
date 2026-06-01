"""Tests for deterministic auditor opinion generation."""
from __future__ import annotations

from aaa.agents.tier2.report_architect import _auditor_opinion


def test_pass_without_material_findings_is_unqualified():
    opinion = _auditor_opinion({"material_findings_count": 0}, "PASS")
    assert opinion["opinion_type"] == "unqualified"
    assert "ISAE 3000" in opinion["methodology_basis"]


def test_pass_with_material_findings_is_qualified():
    opinion = _auditor_opinion(
        {
            "material_findings_count": 1,
            "blocking_findings": [{"finding_id": "F-001", "materiality": "material"}],
        },
        "PASS",
    )
    assert opinion["opinion_type"] == "qualified"
    assert "F-001" in opinion["basis_paragraph"]