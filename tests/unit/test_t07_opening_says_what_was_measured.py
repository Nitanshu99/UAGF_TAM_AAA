"""T-20260914-012: T07 does not say data quality was assessed when nothing was measured."""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t07 import build_t07

_UNMEASURED = {"overall_missingness_pct": None}


def test_no_dataset_no_assessment_claimed() -> None:
    """Case 04: every tool unmeasured, and the narrative says the examination did not happen."""
    narrative = build_t07("eng", {}, _UNMEASURED, {"imbalance_severity": None},
                          {"pii_detected": None}, "NOT_TESTED", "now")["quality_narrative"]
    assert "assessed via automated tools" not in narrative
    assert narrative.startswith("No dataset was loaded") and "not performed" in narrative


def test_a_measurement_is_described_with_its_article_basis() -> None:
    """One measured result is enough to say what was measured, and under which provisions."""
    narrative = build_t07("eng", {}, {"overall_missingness_pct": 0.4}, {}, {"pii_detected": False},
                          "PASS", "now")["quality_narrative"]
    assert narrative.startswith("Data quality measured on the supplied dataset")
    assert "Art. 10(3)" in narrative and "Art. 10(2)(f)" in narrative
