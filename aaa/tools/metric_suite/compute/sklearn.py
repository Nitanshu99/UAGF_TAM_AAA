"""Part 2 of the former ``metric_suite`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.metric_suite.logger import (  # noqa: F401
    _DEFAULT_PRIMARY,
    _sklearn_classification,
    logger,
)


def _compute_sklearn(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    y_proba: Sequence[Any] | None,
    task: str,
) -> dict[str, Any]:
    """Use scikit-learn for metric computation."""
    from sklearn import metrics as skm  # type: ignore

    metrics_out: dict[str, float | None] = {}
    calibration_error: float | None = None
    if task == "classification":
        calibration_error = _sklearn_classification(skm, y_true, y_pred, y_proba, metrics_out)
        primary = "accuracy"
    else:
        try:
            metrics_out["mae"] = float(skm.mean_absolute_error(y_true, y_pred))
            mse = float(skm.mean_squared_error(y_true, y_pred))
            metrics_out["mse"] = mse
            metrics_out["rmse"] = float(mse ** 0.5)
            metrics_out["r2"] = float(skm.r2_score(y_true, y_pred))
        except Exception:
            pass
        primary = "rmse"

    return {
        "primary_metric": primary,
        "primary_metric_value": metrics_out.get(primary),
        "metrics": metrics_out,
        "calibration_error": calibration_error,
        "evaluation_sample_size": len(y_true),
        "metric_suite_tool": "scikit-learn",
    }
