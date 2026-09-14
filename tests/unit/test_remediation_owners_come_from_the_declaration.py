"""Remediation owners come from the declared contacts, or name the role that should own them.

``organisation_contacts`` was in the T01a contract, read by Phase 5 and written by
nobody: no wizard field, no dispatch key, so every roadmap owner in every report
was "To be assigned" (T-20260913-025/042).
"""
from __future__ import annotations

import asyncio
from typing import Any

from aaa.agents.tier1.phases.phase_runners.phase import p5
from aaa.agents.tier2.governance_agent.enrich import enrich_remediation_roadmap
from aaa.agents.tier2.governance_agent.roadmap_rules import DOMAIN_TO_OWNER_FIELD
from aaa.platform.evidence.contract import artefact_schema_errors
from aaa.platform.state.contacts import CONTACT_ROLES, declared_contacts, owner_for


def test_an_undeclared_owner_names_the_role() -> None:
    assert owner_for("technical_lead", {}) == "To be assigned (technical lead)"
    assert owner_for("dpo", {"dpo": "  "}) == "To be assigned (data protection officer)"
    assert owner_for("data_lead", {"data_lead": "Dana Roth"}) == "Dana Roth"


def test_every_domain_owner_is_a_contract_role() -> None:
    import json
    from pathlib import Path

    schema = json.loads(Path("templates/T01a_stage_a_triage.json").read_text(encoding="utf-8"))
    roles = set(schema["properties"]["organisation_contacts"]["properties"])
    assert set(CONTACT_ROLES) == roles
    assert set(DOMAIN_TO_OWNER_FIELD.values()) <= roles
    assert DOMAIN_TO_OWNER_FIELD["D6"] == "technical_lead"


def test_roadmap_rows_are_owned_by_their_domain_role() -> None:
    items = [{"control_id": "C1", "gap_severity": "high"}, {"control_id": "C9", "gap_severity": "low"}]
    rows = enrich_remediation_roadmap(items, {"executive_sponsor": "Managing Director"},
                                      [{"domain_id": "D1"}, {"domain_id": "D6"}])
    assert rows[0]["assigned_owner"] == "Managing Director"
    assert rows[1]["assigned_owner"] == "To be assigned (technical lead)"


def test_declared_contacts_drop_blanks_and_unknown_roles() -> None:
    assert declared_contacts({"dpo": "", "technical_lead": " Ali ", "cto": "x"}) == {
        "technical_lead": "Ali"}
    assert declared_contacts(None) == {}


def test_stage_a_with_contacts_validates() -> None:
    stage_a = {"organisation_contacts": {"technical_lead": "Ali"}}
    errors = artefact_schema_errors("T01a_stage_a_triage", stage_a) or []
    assert not [e for e in errors if "organisation_contacts" in e]


def test_phase5_dispatch_carries_the_declared_contacts(monkeypatch: Any) -> None:
    seen: dict[str, Any] = {}

    async def fake_verify(_agent: Any, dispatch: dict, state: dict, **_: Any):
        seen.update(dispatch["declaration_summary"])
        return None, state

    monkeypatch.setattr(p5, "run_phase_with_verification", fake_verify)
    state = {"engagement_id": "eng", "client_submission": {"stage_a": {
        "organisation_contacts": {"technical_lead": "Ali", "dpo": ""}}}}
    asyncio.run(p5.run_phase_5(object(), state))
    assert seen["organisation_contacts"] == {"technical_lead": "Ali"}


def test_the_wizard_collects_contacts(monkeypatch: Any) -> None:
    from aaa.ui import app

    monkeypatch.setattr(app.st, "session_state", {
        "s3_a_provider_name": "P", "s3_a_system_name": "S", "s3_a_version": "1.0",
        "s3_a_contact_technical_lead": "Ali", "s3_a_contact_dpo": ""})
    assert app._collect_stage_a()["organisation_contacts"] == {"technical_lead": "Ali"}
