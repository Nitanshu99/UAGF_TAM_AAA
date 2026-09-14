"""T-20260914-001: named-entity PII is read from language, not from numbers or codes.

Case 01's scan labelled the integer ``credit_amount`` column DATE_TIME and the code
``radio_tv`` a PERSON — spaCy's entity model applied to values that are not text.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from aaa.tools.pii_scan.scan.aggregate import language_results


@dataclass
class _Hit:
    entity_type: str
    recognition_metadata: dict = field(default_factory=dict)


_NER = _Hit("PERSON", {"recognizer_name": "SpacyRecognizer"})
_CARD = _Hit("CREDIT_CARD", {"recognizer_name": "CreditCardRecognizer"})


def test_ner_guesses_on_numbers_and_codes_are_dropped_patterns_kept() -> None:
    """A number or an identifier keeps only pattern-recognizer results."""
    assert language_results("5823", [_NER, _CARD], numeric=True) == [_CARD]
    assert language_results("radio_tv", [_NER], numeric=False) == []
    assert language_results("Anna Schmidt", [_NER], numeric=False) == [_NER]
    assert language_results("Berlin", [_NER], numeric=False) == [_NER]


def test_case_01_columns_with_the_real_engine() -> None:
    """Presidio and spaCy on the values case 01 holds: nothing from the entity model."""
    pytest.importorskip("presidio_analyzer")
    spacy = pytest.importorskip("spacy")
    if not spacy.util.is_package("en_core_web_lg"):
        pytest.skip("spaCy model en_core_web_lg not installed")
    pd = pytest.importorskip("pandas")
    from aaa.tools.pii_scan import pii_scan

    frame = pd.DataFrame({"credit_amount": [5823, 10329, 2267, 8968, 1169] * 20,
                          "purpose": ["radio_tv", "car_new", "business", "education",
                                      "radio_tv"] * 20,
                          "owner": ["Anna Schmidt", "Jonas Weber", "Lea Fischer",
                                    "Paul Wagner", "Mia Becker"] * 20})
    found = {(e["column_name"], e["entity_type"]) for e in pii_scan(frame)["entities_found"]}
    assert ("credit_amount", "DATE_TIME") not in found and ("purpose", "PERSON") not in found
    assert ("owner", "PERSON") in found
