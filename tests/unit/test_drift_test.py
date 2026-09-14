"""PSI drift detection between training and evaluation datasets (Art. 10)."""
from __future__ import annotations

import pandas as pd
import pytest

from aaa.tools.drift_test import band, drift_test


def _frame(values: list[float], cats: list[str]) -> pd.DataFrame:
    """Build a two-column frame with one numeric and one categorical feature."""
    return pd.DataFrame({"score": values, "region": cats})


def test_identical_distributions_report_no_drift():
    """A frame compared with itself is stable and passes."""
    df = _frame([float(i % 10) for i in range(200)], ["de", "eu"] * 100)
    result = drift_test(reference=df, current=df)
    assert result["computed"] is True
    assert result["verdict"] == "PASS"
    assert result["drifted_features"] == []
    assert result["max_psi"] < 0.1


def test_shifted_numeric_feature_is_flagged():
    """A clearly shifted numeric feature exceeds the 0.2 alert threshold."""
    ref = _frame([float(i % 10) for i in range(200)], ["de"] * 200)
    cur = _frame([float(50 + i % 10) for i in range(200)], ["de"] * 200)
    result = drift_test(reference=ref, current=cur)
    assert result["verdict"] == "FAIL"
    assert "score" in result["drifted_features"]


def test_shifted_categorical_feature_is_flagged():
    """A categorical distribution flip is detected on the discrete path."""
    ref = _frame([1.0] * 100, ["de"] * 90 + ["eu"] * 10)
    cur = _frame([1.0] * 100, ["de"] * 10 + ["eu"] * 90)
    result = drift_test(reference=ref, current=cur)
    assert result["verdict"] == "FAIL"
    assert "region" in result["drifted_features"]
    assert any(f["kind"] == "categorical" for f in result["features"])


@pytest.mark.parametrize("psi,expected", [
    (0.0, "stable"),
    (0.099, "stable"),
    (0.1, "moderate_shift"),          # STABLE is exclusive
    (0.199, "moderate_shift"),
    (0.2, "significant_shift"),       # MODERATE is exclusive
    (5.0, "significant_shift"),
])
def test_band_labels_the_conventional_psi_thresholds(psi, expected):
    """The 0.1 / 0.2 PSI cut-points map to the three stability bands."""
    assert band(psi) == expected
