"""A column is labelled with an entity only when enough of its cells carry it.

Case 06's T08 logged racial-or-ethnic-origin data because spaCy read a joined
string of job IDs as a nationality/religious/political group (T-20260913-012).
The aggregation is pure, so these run without spaCy; the last test runs the real
engine where it is installed.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from aaa.tools.pii_scan.logger import MIN_COLUMN_RATE, MIN_ENTITY_SCORE
from aaa.tools.pii_scan.scan.aggregate import column_entities
from aaa.tools.pii_scan.scan.presidio import _sample


@dataclass
class _Hit:
    entity_type: str
    score: float = 0.85


def test_an_id_column_with_two_stray_hits_is_not_labelled() -> None:
    """2 of 200 cells is noise, not a nationality column."""
    cells = [[_Hit("NRP")]] * 2 + [[]] * 198
    assert not column_entities(cells, 200)


def test_a_free_text_column_where_many_cells_carry_it_is_labelled() -> None:
    """42% of CVs naming a nationality is a real detection; the count is cells, not spans."""
    cells = [[_Hit("NRP"), _Hit("NRP")]] * 84 + [[]] * 116
    assert column_entities(cells, 200) == {"NRP": 84}


def test_low_confidence_results_are_dropped() -> None:
    """A 0.05 bank-number guess on every numeric cell labels nothing."""
    cells = [[_Hit("US_BANK_NUMBER", score=0.05)]] * 200
    assert not column_entities(cells, 200)


def test_the_thresholds_are_the_documented_ones() -> None:
    """Changing either changes what T07/T08 report across cases; it must be deliberate."""
    assert (MIN_ENTITY_SCORE, MIN_COLUMN_RATE) == (0.5, 0.10)


def test_the_sample_is_seeded_not_the_first_rows() -> None:
    """Sorted files make head() unrepresentative; the same frame samples the same rows."""
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"x": range(1000)})
    first, second = _sample(df, 200), _sample(df, 200)
    assert list(first.index) == list(second.index) and list(first.index) != list(range(200))


def test_job_ids_are_not_a_special_category_with_the_real_engine() -> None:
    """The case-06 false positive, against Presidio and spaCy themselves."""
    pytest.importorskip("presidio_analyzer")
    spacy = pytest.importorskip("spacy")
    if not spacy.util.is_package("en_core_web_lg"):
        pytest.skip("spaCy model en_core_web_lg not installed")
    pd = pytest.importorskip("pandas")
    from aaa.tools.pii_scan import pii_scan

    df = pd.DataFrame({"job_id": [f"JOB-{i:04d}" for i in range(200)]})
    assert pii_scan(df)["special_category_data_detected"] is False
