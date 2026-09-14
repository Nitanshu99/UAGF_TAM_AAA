"""T-20260913-096: a Presidio NRP match is not racial-or-ethnic-origin data.

NRP is spaCy's NORP — "a nationality, religious or political group" — and spaCy
gives that label to language names too. Case 05's CVs say "fluent in german and
english"; the scan recorded racial_or_ethnic_origin, contradicted the provider's
correct declaration and sent T06/T07/T08 to human review.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.tools.pii_scan.logger import (
    _HIGH_SEVERITY_ENTITIES,
    _SPECIAL_CATEGORY_ENTITIES,
    _UNRESOLVED_ENTITIES,
)
from aaa.tools.pii_scan.scan.aggregate import matched_terms, unresolved_mention
from tests.unit.support.nrp_hits import CV as _CV
from tests.unit.support.nrp_hits import nrp_hits as _hits


def test_nrp_asserts_no_category_and_is_not_high_severity() -> None:
    """The entity cannot say which group it found, so it names no Art. 9 category."""
    assert "NRP" not in _SPECIAL_CATEGORY_ENTITIES and "NRP" in _UNRESOLVED_ENTITIES
    assert "NRP" not in _HIGH_SEVERITY_ENTITIES
    assert _SPECIAL_CATEGORY_ENTITIES["RACE"] == "racial_or_ethnic_origin"


def test_matched_terms_are_recorded_most_frequent_first() -> None:
    """The reader sees what matched: the words, lower-cased, by frequency."""
    cells = [_CV, _CV, "German and English correspondence."]
    results = [_hits(_CV, "german", "english"), _hits(_CV, "german"),
               _hits(cells[2], "German")]
    assert matched_terms(cells, results, "NRP") == ["german", "english"]
    mention = unresolved_mention("cv_text", "NRP", 3, cells, results)
    assert mention is not None
    assert mention["matched_terms"] == ["german", "english"] and mention["sample_count"] == 3
    assert unresolved_mention("cv_text", "RACE", 3, cells, results) is None


def test_unresolved_mentions_fit_the_t07_schema() -> None:
    """The new field is in both template copies and validates."""
    jsonschema = pytest.importorskip("jsonschema")
    root = Path(__file__).resolve().parents[2]
    copies = [root / "templates/T07_data_quality_report.json",
              root / "packages/uagf_tam_templates/src/uagf_tam_templates/schemas/"
                     "T07_data_quality_report.json"]
    schemas = [json.loads(p.read_text()) for p in copies]
    assert schemas[0] == schemas[1]
    sub = schemas[0]["properties"]["pii_scan"]
    cells = [_CV]
    scan = {"pii_detected": True, "special_category_data_detected": False,
            "entities_found": [{"entity_type": "NRP", "column_name": "cv_text",
                                "sample_count": 1, "severity": "medium"}],
            "unresolved_mentions": [unresolved_mention(
                "cv_text", "NRP", 1, cells, [_hits(_CV, "german")])]}
    jsonschema.validators.validator_for(schemas[0])(sub).validate(scan)
