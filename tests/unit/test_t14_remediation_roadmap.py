"""T14's roadmap is the CGSA roadmap, and enrichment follows what the CGSA says.

Case 06 printed 36 rows with an empty ``control_name``, five keys the schema
forbids, no ``action`` or ``eu_ai_act_article`` (108 schema errors), and 52-week
deadlines on gaps the source gave 4 and 2 weeks (T-20260913-006/007/008). The
payload here is synthetic, in the same CGSA dialect, so CI can run it.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from aaa.agents.tier2.governance_agent.enrich import enrich_remediation_roadmap
from aaa.agents.tier2.governance_agent.roadmap_rules import control_domains
from aaa.agents.tier2.governance_agent.t14.remediation import remediation_section
from aaa.tools.cgsa_ingest import IngestResult, _normalise_remediation
from tests.unit.support.cgsa_roadmap_fixture import PAYLOAD, ROWS

SCHEMA = json.loads(Path("templates/T14_governance_findings.json").read_text(encoding="utf-8"))


def _t14_rows() -> list[dict]:
    state = {"remediation_roadmap": _normalise_remediation(ROWS)}
    return remediation_section(IngestResult(payload=PAYLOAD, state_delta=state))


def test_the_roadmap_validates_against_the_t14_schema() -> None:
    """Zero errors against the section's own schema, which forbids extra keys."""
    validator = jsonschema.Draft202012Validator(SCHEMA["properties"]["remediation_roadmap"])
    errors = [e.message for e in validator.iter_errors(_t14_rows())]
    assert not errors, errors


def test_the_roadmap_is_the_source_in_order_with_names() -> None:
    """Every row named as the CGSA names it, in the CGSA's order."""
    rows = _t14_rows()
    assert [r["control_name"] for r in rows] == [r["control_name"] for r in ROWS]
    assert rows[1]["timeline_weeks"] == 4 and rows[2]["timeline_weeks"] is None


def test_state_carries_the_source_fields_beside_the_derived_ones() -> None:
    """Consumers of the old keys keep them; the source's own fields survive ingest."""
    item = _normalise_remediation(ROWS)[1]
    assert item["recommended_action"] == "Record lineage."
    assert (item["control_name"], item["timeline_weeks"], item["eu_ai_act_article"]) == (
        "Data Lineage", 4, "Article 10")


def test_enrichment_takes_the_sources_timeline_and_resolves_the_domain() -> None:
    """A high gap the source dates at 4 weeks is due in 4, owned by its domain's lead."""
    items = enrich_remediation_roadmap(_normalise_remediation(ROWS), {"data_lead": "Dana"},
                                       ROWS, control_domains(PAYLOAD))
    assert (items[1]["priority_label"], items[1]["deadline_weeks"]) == ("short_term", 4)
    assert items[1]["domain_id"] == "D2" and items[1]["assigned_owner"] == "Dana"
    assert (items[2]["priority_label"], items[2]["deadline_weeks"]) == ("medium_term", 26)


def test_an_explicit_domain_still_wins_and_the_legacy_dialect_still_maps() -> None:
    """A source ``domain_id`` beats the tree; ``major`` and ``observation`` keep their meaning."""
    items = [{"control_id": "C12", "gap_severity": "major"},
             {"control_id": "C12", "gap_severity": "observation"}]
    source = [{"domain_id": "D6"}, {}]
    out = enrich_remediation_roadmap(items, {}, source, control_domains(PAYLOAD))
    assert out[0]["domain_id"] == "D6" and out[1]["domain_id"] == "D4"
    assert [o["priority_label"] for o in out] == ["short_term", "long_term"]
