"""T-20260913-097: a declared training-data description is about the training data.

Case 05's intake calls its training data a "screening corpus"; T06 required each
sentence to say "training set" and grounded 0 of 8 questions, and its year range
"2024–2025" was not a collection window to the ISO-only pattern.
"""
from __future__ import annotations

import re

from aaa.agents.tier2.data_auditor.t06 import t06_questions
from aaa.tools.document_evidence import DATE_RANGE, gather_evidence, ground

_DESCRIPTION = ("TalentSift screening corpus — 240 anonymised CV summaries from 2024–2025 "
                "recruitment campaigns across office, logistics and engineering vacancy families.")


def _no_documents(*_args, **_kwargs) -> list:
    return []


def test_the_declared_field_grounds_the_training_questions() -> None:
    """Timeframe and pre-processing are quoted from the field; nothing is invented."""
    found = gather_evidence("", t06_questions("training"),
                            declared={"training_data_description": _DESCRIPTION},
                            search=_no_documents)
    timeframe, preprocessing = found["timeframe"], found["preprocessing"]
    assert timeframe and preprocessing and "anonymised" in preprocessing.quote
    assert timeframe.origin == "Annex IV dossier, training_data_description"
    assert found["acquisition"] is None and found["consent"] is None


def test_the_same_sentence_elsewhere_must_name_the_dataset() -> None:
    """From an uploaded document, or about the evaluation set, it answers nothing."""
    questions = {q.key: q for q in t06_questions("training")}
    passage = {"text": _DESCRIPTION, "source_uri": "minio://eng/docs/plan.txt", "score": 1.0}
    assert ground([passage], questions["preprocessing"]) is None
    evaluation = gather_evidence("", t06_questions("evaluation"),
                                 declared={"training_data_description": _DESCRIPTION},
                                 search=_no_documents)
    assert not any(evaluation.values())


def test_a_year_range_is_a_collection_window() -> None:
    """Years and ISO months match; a single year-month does not."""
    years, hyphenated = (re.search(DATE_RANGE, "from 2024–2025 recruitment"),
                         re.search(DATE_RANGE, "sales data, 2022-2025."))
    assert years and years.group(0) == "2024–2025"
    assert hyphenated and hyphenated.group(0) == "2022-2025"
    assert re.search(DATE_RANGE, "2026-01-01 to 2026-08-31")
    assert not re.search(DATE_RANGE, "released 2024-05 as v1.2")
