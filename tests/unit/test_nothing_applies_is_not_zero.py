"""T-094/T-095: a score or KPI the audit did not produce is never shown as zero.

Case 02 (a minimal-risk sales forecaster, bound by no article) rendered
"Conformity 0/100" and "Requirements met 0/0" on its results page — a default
zero displayed as a measurement for a system that was never scored.
"""
from __future__ import annotations

from aaa.tools.report_render.pdf.cover import kpi_text
from aaa.ui.styles.gauge import score_gauge
from aaa.ui.wizard.step4.header import article_score
from aaa.ui.wizard.step4.kpis import matrix_counts
from aaa.ui.wizard.step4.tiles import kpi_tiles


def test_no_applicable_article_has_no_score() -> None:
    """Nothing to score is ``None``; not-tested rows are excluded like the tiles do."""
    assert article_score({}) is None
    assert article_score({"Art.50": "NOT_APPLICABLE", "Art.9": "PENDING"}) is None
    assert article_score({"Art.9": "NOT_TESTED", "Art.13": "PASS"}) == 100.0
    assert article_score({"Art.13": "INSUFFICIENT_EVIDENCE"}) == 0.0


def test_gauge_without_a_score_draws_no_number() -> None:
    """The gauge says not applicable, with the bare track and no 0.

    No value arc at all: a zero-length round-capped dash paints a dot at zero.
    """
    markup = score_gauge(None, "Conformity", "PASS_WITH_OBSERVATIONS")
    assert "not applicable" in markup and "—" in markup
    assert "aaa-arc" not in markup and "stroke-dasharray" not in markup
    assert ">0<" not in markup and "/ 100" not in markup


def test_gauge_caption_sits_below_the_track() -> None:
    """The caption baseline clears the track's round ends (y = 60 + 10/2)."""
    for score in (None, 0.0, 72.0):
        markup = score_gauge(score, "Conformity", "PASS")
        caption_y = float(markup.rsplit('<text x="60" y="', 1)[1].split('"', 1)[0])
        assert caption_y - 7 * 0.75 >= 65  # font-size 7, cap height ≈ 0.75 em


def test_tiles_for_an_engagement_bound_by_no_article() -> None:
    """No ``0/100``, no ``0/0``, no meter; an absent intake score is not 0%."""
    final = {"compliance_matrix": {}, "intake_completeness_score": None}
    tiles = kpi_tiles(final, matrix_counts({}))
    joined = "".join(tiles)
    assert "/100" not in joined and "/0" not in joined
    assert "No EU AI Act article applies" in tiles[0]
    assert "aaa-meter" not in tiles[0] + tiles[1] + tiles[3]
    assert "Not measured" in tiles[3] and ">0<" not in tiles[3]


def test_tiles_with_applicable_articles_are_unchanged() -> None:
    """Scored engagements keep their numbers."""
    matrix = {"Art.10": "FAIL", "Art.13": "PASS"}
    tiles = kpi_tiles({"compliance_matrix": matrix, "intake_completeness_score": 0.9},
                      matrix_counts(matrix))
    assert ">50<" in tiles[0] and "/100" in tiles[0]
    assert "/2" in tiles[1] and ">90<" in tiles[3]


def test_pdf_cover_kpi_absent_is_not_measured() -> None:
    """Missing or ``None`` KPIs read "not measured"; present values format as before."""
    assert kpi_text({}, "completeness_score", "kpi1_band") == "not measured"
    assert kpi_text({"completeness_score": None}, "completeness_score",
                    "kpi1_band") == "not measured"
    assert kpi_text({"regulatory_coverage_pct": 100, "kpi2_band": "GREEN"},
                    "regulatory_coverage_pct", "kpi2_band", ".1f", "%") == "100.0%  (GREEN)"
