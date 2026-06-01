"""Tests for Phase 6 management-response shell generation."""
from __future__ import annotations

from aaa.agents.tier2.report_architect import _management_response_shell


def test_management_response_shell_includes_only_material_findings():
    findings = [
        {
            "finding_id": "F-001",
            "control_id": "C1",
            "description": "Major governance gap",
            "materiality": "material",
        },
        {"finding_id": "F-002", "description": "Observation", "materiality": "not_material"},
    ]
    remediation = [{"control_id": "C1", "gap_detail": "Close the gap", "assigned_owner": "DPO"}]

    shell = _management_response_shell(findings, remediation)

    assert len(shell) == 1
    assert shell[0]["finding_id"] == "F-001"
    assert shell[0]["auditor_recommendation"] == "Close the gap"
    assert shell[0]["management_response"] == "[Management response pending]"
    assert shell[0]["responsible_owner"] == "DPO"