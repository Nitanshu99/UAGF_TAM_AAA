"""Part 1 of the former ``metric_suite`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


_DEFAULT_PRIMARY = {
    "classification": "accuracy",
    "regression": "rmse",
}


def _sklearn_classification(skm: Any, y_true, y_pred, y_proba,
                            metrics_out: dict) -> float | None:
    """Fill classification metrics; return the calibration error if computed."""
    calibration_error: float | None = None
    metrics_out["accuracy"] = float(skm.accuracy_score(y_true, y_pred))
    try:
        metrics_out["f1_macro"] = float(
            skm.f1_score(y_true, y_pred, average="macro", zero_division=0))
        metrics_out["precision_macro"] = float(
            skm.precision_score(y_true, y_pred, average="macro", zero_division=0))
        metrics_out["recall_macro"] = float(
            skm.recall_score(y_true, y_pred, average="macro", zero_division=0))
    except Exception:
        pass
    if y_proba is not None and len(y_proba) == len(y_true):
        try:
            metrics_out["roc_auc"] = float(skm.roc_auc_score(y_true, y_proba))
        except Exception:
            metrics_out["roc_auc"] = None
        try:
            metrics_out["brier_score"] = float(skm.brier_score_loss(y_true, y_proba))
            calibration_error = metrics_out["brier_score"]
        except Exception:
            pass
    return calibration_error
