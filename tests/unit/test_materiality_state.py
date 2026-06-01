"""Regression tests for materiality fields in audit state types."""
from __future__ import annotations

from aaa.platform.state import AuditState, Finding, RemediationItem


def test_materiality_fields_are_declared_on_state_types():
    assert "materiality" in Finding.__annotations__
    assert "materiality_rationale" in Finding.__annotations__
    assert "materiality" in RemediationItem.__annotations__
    assert "materiality_rationale" in RemediationItem.__annotations__
    assert "assigned_owner" in RemediationItem.__annotations__
    assert "deadline_weeks" in RemediationItem.__annotations__
    assert "priority_label" in RemediationItem.__annotations__
    assert "material_findings_count" in AuditState.__annotations__
    assert "possibly_material_findings_count" in AuditState.__annotations__