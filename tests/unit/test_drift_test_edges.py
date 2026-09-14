"""Drift-test edge cases: fail-soft paths, bands, and skipped columns."""
from __future__ import annotations

import pandas as pd

from aaa.tools.drift_test import band, drift_test


def test_missing_frame_is_fail_soft():
    """A missing dataset yields NOT_COMPUTED rather than raising."""
    result = drift_test(reference=None,
                        current=pd.DataFrame({"a": [1.0]}))
    assert result["computed"] is False
    assert result["verdict"] == "NOT_COMPUTED"
    assert "unavailable" in result["reason"]


def test_no_overlapping_columns_is_fail_soft():
    """Disjoint schemas cannot be compared and say so."""
    result = drift_test(reference=pd.DataFrame({"a": [1, 2]}),
                        current=pd.DataFrame({"b": [1, 2]}))
    assert result["computed"] is False
    assert "overlapping" in result["reason"]


def test_band_thresholds():
    """Bands follow the conventional PSI cut-offs."""
    assert band(0.05) == "stable"
    assert band(0.15) == "moderate_shift"
    assert band(0.5) == "significant_shift"


def test_identifier_and_free_text_columns_are_not_comparable():
    """High-cardinality discrete columns are skipped, not reported as drift."""
    ref = pd.DataFrame({"applicant_id": [f"A{i}" for i in range(100)],
                        "cv_text": [f"unique resume text {i}" for i in range(100)],
                        "sex": ["f", "m"] * 50})
    cur = pd.DataFrame({"applicant_id": [f"B{i}" for i in range(100)],
                        "cv_text": [f"other resume text {i}" for i in range(100)],
                        "sex": ["f", "m"] * 50})
    result = drift_test(reference=ref, current=cur)
    skipped = {f["feature"] for f in result["features"] if f["band"] == "not_comparable"}
    assert skipped == {"applicant_id", "cv_text"}
    assert result["drifted_features"] == []
    assert result["verdict"] == "PASS"
