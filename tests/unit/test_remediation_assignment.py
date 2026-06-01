"""Tests for owner, deadline and priority assignment on remediation items."""
from __future__ import annotations

from aaa.agents.tier2.governance_agent import GovernanceAgent


def test_remediation_assignment_uses_domain_contacts_and_severity():
    items = [{"rank": 1, "control_id": "C1", "gap_severity": "critical"}]
    source = [{"domain_id": "D2", "gap_severity": "critical"}]
    contacts = {"data_lead": "Data Governance Lead"}

    enriched = GovernanceAgent._enrich_remediation_roadmap(items, contacts, source)

    assert enriched[0]["assigned_owner"] == "Data Governance Lead"
    assert enriched[0]["priority_label"] == "immediate"
    assert enriched[0]["deadline_weeks"] == 4