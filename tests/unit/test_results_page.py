"""Unit tests for the results-page score computation and gauge markup."""
from __future__ import annotations

from aaa.ui.styles.gauge import score_gauge
from aaa.ui.wizard.step4.header import article_score


def test_article_score_weights_verdicts() -> None:
    """PASS=1, PASS_WITH_OBSERVATIONS=0.5, FAIL=0, NOT_APPLICABLE excluded."""
    matrix = {"Art.10": "FAIL", "Art.13": "PASS",
              "Art.14": "PASS_WITH_OBSERVATIONS", "Art.50": "NOT_APPLICABLE"}
    assert article_score(matrix) == 50.0


def test_article_score_empty_matrix_has_no_score() -> None:
    """An empty or fully non-applicable matrix has nothing to score (T-094)."""
    assert article_score({}) is None
    assert article_score({"Art.50": "NOT_APPLICABLE"}) is None


def test_score_gauge_markup() -> None:
    """The gauge embeds the clamped score, label, and verdict colour."""
    markup = score_gauge(72.4, "Article conformity", "FAIL")
    assert "<svg" in markup and "72" in markup
    # The arc takes its colour from the palette token, not a literal hex, so
    # the gauge and every other verdict surface cannot drift apart.
    assert "var(--bad)" in markup  # FAIL arc colour
    assert "Article conformity" in markup
    assert "150" not in score_gauge(150, "x", "PASS")  # clamped to 100
