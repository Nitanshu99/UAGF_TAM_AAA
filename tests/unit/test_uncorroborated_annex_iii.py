"""T-20260914-004: a declared Annex III section the intake does not evidence is said and recorded.

Case 03 declared Annex III §2 for harbour-crane telemetry; T03 read "Verified risk
tier: high" beside the classifier's "no supporting term in the intake text".
"""
from __future__ import annotations

import json
from pathlib import Path

from aaa.agents.tier2.scope_agent.t02_t03 import build_t03
from aaa.agents.tier2.scope_agent.uncorroborated import uncorroborated_finding
from aaa.tools.annex_iii_classify import annex_iii_classify

_MOCK = Path(__file__).resolve().parents[2] / "mock"


def _entries(case: str) -> list:
    stage_a = json.loads((_MOCK / case / "stage_a.json").read_text())
    return annex_iii_classify(declared_sections=stage_a["declared_annex_iii_sections"],
                              system_description=stage_a["intended_purpose"])


def test_case_03_tier_is_declared_not_verified_and_an_observation_is_raised() -> None:
    """The tier stays high; the narrative and a possibly-material finding say why it is not verified."""
    entries = _entries("03_harbourlogistik_gmbh")
    narrative = build_t03("eng", entries, "high", False, "now")["classification_narrative"]
    assert "Verified risk tier" not in narrative and "Risk tier: high" in narrative
    assert "has not corroborated the classification" in narrative
    finding = uncorroborated_finding(entries)
    assert finding is not None and finding["materiality"] == "possibly_material"
    assert set(finding["eu_ai_act_articles"]) == {"Art.6", "Annex_III"}


def test_an_evidenced_declaration_is_verified_and_raises_nothing() -> None:
    """Case 05's CV screener evidences Annex III §4 in its own words."""
    entries = _entries("05_talentsift_gmbh")
    assert "Verified risk tier: high" in build_t03("eng", entries, "high", False,
                                                   "now")["classification_narrative"]
    assert uncorroborated_finding(entries) is None
