"""T-20260914-056 and -059: T14 keeps every mapped article; reconciliation counts every scored control."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from aaa.agents.tier2.governance_agent.reconcile import reconcile_cgsa
from aaa.agents.tier2.governance_agent.t14.blocking import blocking_findings_section

_SCHEMA = json.loads(Path("templates/T14_governance_findings.json").read_text(encoding="utf-8"))


def test_a_blocking_finding_carries_every_article_its_control_maps_to() -> None:
    """C02 names Art. 9 and Art. 5; T14 used to keep Art. 9 alone."""
    rows = blocking_findings_section({"blocking_findings": [
        {"control_id": "C02", "control_name": "Legal applicability", "finding": "Score 2 of 3.",
         "eu_ai_act_article": "Article 9", "eu_ai_act_articles": ["Article 9", "Article 5"],
         "remediation_action": "Add a gate.", "gap_severity": "critical"},
        {"control_id": "C10", "control_name": "Data quality", "finding": "Score 1 of 3.",
         "eu_ai_act_article": "Article 10", "remediation_action": "Profile data."}]})
    assert rows[0]["eu_ai_act_articles"] == ["Article 9", "Article 5"]
    assert "eu_ai_act_articles" not in rows[1]
    item = _SCHEMA["properties"]["blocking_findings"]["items"]
    for row in rows:
        jsonschema.validate(row, item)


def _control(cid: str, score: int, threshold: int | None, constraint: bool) -> dict:
    """A scored control; *constraint* says whether a hard constraint applies to it."""
    return {"control_id": cid, "maturity_score": score, "final_maturity_score": score,
            "threshold_score": threshold,
            "hard_constraint": {"applicable": constraint, "threshold_score": 3 if constraint else None}}


def test_below_threshold_controls_outside_the_hard_constraints_are_identified() -> None:
    """Evaluated export: one constraint breach and one soft gap make the reported two."""
    payload = {"overall_scores": {"controls_assessed": 3, "controls_below_threshold": 2},
               "domains": [{"controls": [_control("C01", 2, 3, False), _control("C02", 1, 3, True),
                                         _control("C12", 3, 3, True)]}]}
    assert [f["finding_id"] for f in reconcile_cgsa(payload)] == []


def test_a_control_without_its_own_threshold_stays_unidentified() -> None:
    """Self-assessment export: a soft gap with no threshold cannot be named below it."""
    payload = {"overall_scores": {"controls_assessed": 2, "controls_below_threshold": 2},
               "domains": [{"controls": [_control("C01", 2, None, False),
                                         _control("C02", 1, None, True)]}]}
    assert [f["finding_id"] for f in reconcile_cgsa(payload)] == ["P5-CGSA-BELOW"]
