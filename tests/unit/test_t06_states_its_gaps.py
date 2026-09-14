"""T-20260913-105: T06 states what was not documented, by Art. 10(2) point.

Case 05's Verifier read null text fields beside "Not declared" ones as fields the
builder left out, and escalated the datasheet asking for gaps mapped to Art. 10(2).
"""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t06 import build_t06
from aaa.platform.evidence.contract import artefact_schema_errors
from tests.unit.support.case06_like_dossier import STAGE_B, T01A
from tests.unit.support.provider_documents import NOW, ev

_FOUND = {"timeframe": ev("240 anonymised CV summaries from 2024–2025 campaigns."),
          "preprocessing": ev("240 anonymised CV summaries from 2024–2025 campaigns.")}


def test_undeclared_text_reads_not_declared_and_unknown_facts_stay_null() -> None:
    """One wording for "nothing declared"; booleans no document settles are null."""
    t06 = build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW, found=_FOUND)
    collection, prep = t06["collection_process"], t06["preprocessing_cleaning_labelling"]
    for text in (collection["consent_mechanism"], collection["third_party_sources"],
                 prep["labelling_description"], prep["software_used"],
                 t06["maintenance"]["retention_period"]):
        assert text.startswith("Not declared")
    assert prep["preprocessing_description"].startswith("Provider statement")
    assert collection["consent_obtained"] is None and prep["raw_data_available"] is None
    assert not artefact_schema_errors("T06_datasheet_for_datasets", t06)


def test_the_notes_name_each_gap_under_its_article_10_2_point() -> None:
    """(b) collection and origin, (c) preparation — only what nothing answered."""
    notes = build_t06("eng", T01A, STAGE_B, {"stage_b": STAGE_B}, NOW,
                      found=_FOUND)["art10_compliance_notes"]
    assert ("Art. 10(2)(b) data collection processes and origin: how the data was acquired, "
            "third-party sources, the consent mechanism for personal data") in notes
    assert "Art. 10(2)(c) data-preparation operations: labelling and annotation" in notes
    assert "the collection period" not in notes and "pre-processing" not in notes
