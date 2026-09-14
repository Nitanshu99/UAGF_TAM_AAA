"""T-20260913-104: the results list counts articles, with each paragraph inside its article.

Case 05's page listed Art.10 as "Not met" and Art.10§2(f) as "Could not be checked · 2"
under a tile that said "1 could not be checked".
"""
from __future__ import annotations

from aaa.ui.wizard.step4.articles import grouped_rows
from aaa.ui.wizard.step4.header import article_parts
from aaa.ui.wizard.step4.kpis import matrix_counts

_CASE_05 = {"Art.10": "FAIL", "Art.10§2(f)": "INSUFFICIENT_EVIDENCE",
            "Art.13": "INSUFFICIENT_EVIDENCE", "Art.14": "PASS_WITH_OBSERVATIONS",
            **{f"Art.{n}": "PASS" for n in (9, 11, 12, 15, 16, 17, 26, 43, 47, 49, 72)}}


def test_group_counts_are_the_tiles_counts() -> None:
    """One article not met, one unchecked, one with observations, eleven met."""
    groups = dict(grouped_rows(_CASE_05))
    counts = matrix_counts(_CASE_05)
    assert len(groups["Not met"]) == counts["unmet"] == 1
    assert len(groups["Could not be checked"]) == counts["unknown"] == 1
    assert len(groups["Met"]) == counts["met"] == 11


def test_the_paragraph_is_shown_inside_its_article_with_its_own_outcome() -> None:
    """Art.10§2(f) renders in Art.10's row, not in another group."""
    groups = dict(grouped_rows(_CASE_05))
    assert "Art.10§2(f)" in groups["Not met"][0]
    assert "Could not be checked" in groups["Not met"][0]  # the paragraph's own pill
    assert not any("Art.10§2(f)" in row for row in groups["Could not be checked"])


def test_a_paragraph_without_its_article_stands_alone() -> None:
    """No verdict is dropped when the parent article has no row."""
    parts = article_parts({"Art.15§1": "PASS", "Art.13": "FAIL"})
    assert parts == {"Art.13": ("FAIL", []), "Art.15§1": ("PASS", [])}
