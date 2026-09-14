"""T-20260913-096: T08 and the real scanner on case 05's CV phrasing.

The mention stays visible with the words it matched; it is not a detected
special category, so nothing contradicts the provider's declaration.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier2.data_auditor.t08 import build_t08
from aaa.tools.pii_scan.scan.aggregate import unresolved_mention
from tests.unit.support.nrp_hits import CV as _CV
from tests.unit.support.nrp_hits import nrp_hits as _hits


def test_t08_names_the_terms_and_records_no_special_category() -> None:
    """Absent as declared, no review flag, and the matched words in the narrative."""
    scan = {"special_category_data_detected": False, "special_categories_found": [],
            "analyser_engine": "presidio",
            "unresolved_mentions": [unresolved_mention(
                "cv_text", "NRP", 29, [_CV], [_hits(_CV, "german", "english")])]}
    t08 = build_t08("eng-05", False, scan, False, "now")
    assert t08["special_category_data_present"] is False
    assert t08["special_categories_detected"] == [] and not t08["hitl_review_required"]
    assert "matched terms: german, english" in t08["compliance_narrative"]
    assert "no category is recorded" in t08["compliance_narrative"]


def test_case_05_phrasing_with_the_real_engine() -> None:
    """Presidio and spaCy themselves, on the sentences case 05's CVs contain."""
    pytest.importorskip("presidio_analyzer")
    spacy = pytest.importorskip("spacy")
    if not spacy.util.is_package("en_core_web_lg"):
        pytest.skip("spaCy model en_core_web_lg not installed")
    pd = pytest.importorskip("pandas")
    from aaa.tools.pii_scan import pii_scan

    texts = [f"clerk with {i} years of experience. fluent in german and english."
             if i % 2 else f"assistant. german and english correspondence. team {i}."
             for i in range(60)]
    result = pii_scan(pd.DataFrame({"cv_text": texts}))
    assert result["special_category_data_detected"] is False
    assert result["special_categories_found"] == []
    # spaCy labels the languages NORP, as it did in the run; the words stay visible.
    nrp = [m for m in result["unresolved_mentions"] if m["entity_type"] == "NRP"]
    assert nrp and nrp[0]["matched_terms"][:2] == ["german", "english"]
    assert all(e["severity"] != "high" for e in result["entities_found"]
               if e["entity_type"] == "NRP")
