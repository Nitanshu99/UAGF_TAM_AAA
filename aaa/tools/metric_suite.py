"""
metric_suite — Performance-metric computation wrapper (§4.2).

Returns a structured dict compatible with the T09_model_card
``performance_metrics`` block.

Production path:  scikit-learn metrics + (optional) torchmetrics.
Offline/fallback: pure-Python accuracy / F1 / AUC implementations.

Usage
-----
    from src.tools.metric_suite import metric_suite

    metrics = metric_suite(y_true, y_pred, y_proba=None, task="classification")
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

_DEFAULT_PRIMARY = {
    "classification": "accuracy",
    "regression": "rmse",
}


def metric_suite(
    y_true: Sequence[Any] | None = None,
    y_pred: Sequence[Any] | None = None,
    y_proba: Sequence[Any] | None = None,
    task: str = "classification",
) -> dict[str, Any]:
    """
    Compute performance metrics for a classifier or regressor.

    Parameters
    ----------
    y_true:
        Ground-truth labels.  Empty / None → returns an empty-result stub.
    y_pred:
        Predicted labels.
    y_proba:
        Predicted probabilities for the positive class (binary classification),
        used for AUC + calibration.  Optional.
    task:
        ``"classification"`` or ``"regression"``.

    Returns
    -------
    dict matching the T09 ``performance_metrics`` sub-schema:
        {
            primary_metric, primary_metric_value, metrics,
            calibration_error, evaluation_sample_size, metric_suite_tool
        }
    """
    if y_true is None or y_pred is None or len(y_true) == 0 or len(y_pred) == 0:
        return _empty_result(task)

    try:
        return _compute_sklearn(y_true, y_pred, y_proba, task)
    except Exception as exc:
        logger.info("scikit-learn unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_true, y_pred, y_proba, task)


# ---------------------------------------------------------------------------
# scikit-learn path
# ---------------------------------------------------------------------------

def _compute_sklearn(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    y_proba: Sequence[Any] | None,
    task: str,
) -> dict[str, Any]:
    """Use scikit-learn for metric computation."""
    from sklearn import metrics as skm  # type: ignore

    n = len(y_true)
    metrics_out: dict[str, float | None] = {}
    calibration_error: float | None = None

    if task == "classification":
        metrics_out["accuracy"] = float(skm.accuracy_score(y_true, y_pred))
        try:
            metrics_out["f1_macro"] = float(
                skm.f1_score(y_true, y_pred, average="macro", zero_division=0)
            )
            metrics_out["precision_macro"] = float(
                skm.precision_score(y_true, y_pred, average="macro", zero_division=0)
            )
            metrics_out["recall_macro"] = float(
                skm.recall_score(y_true, y_pred, average="macro", zero_division=0)
            )
        except Exception:
            pass
        if y_proba is not None and len(y_proba) == n:
            try:
                metrics_out["roc_auc"] = float(skm.roc_auc_score(y_true, y_proba))
            except Exception:
                metrics_out["roc_auc"] = None
            try:
                metrics_out["brier_score"] = float(skm.brier_score_loss(y_true, y_proba))
                calibration_error = metrics_out["brier_score"]
            except Exception:
                pass
        primary = "accuracy"
    else:
        # Regression
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
        "evaluation_sample_size": n,
        "metric_suite_tool": "scikit-learn",
    }


# ---------------------------------------------------------------------------
# Pure-Python fallback
# ---------------------------------------------------------------------------

def _compute_python(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    y_proba: Sequence[Any] | None,
    task: str,
) -> dict[str, Any]:
    """Pure-Python accuracy / F1 / RMSE with no external dependencies."""
    n = len(y_true)
    metrics_out: dict[str, float | None] = {}

    if task == "classification":
        correct = sum(1 for a, b in zip(y_true, y_pred) if a == b)
        accuracy = correct / n if n else 0.0
        metrics_out["accuracy"] = accuracy
        metrics_out["f1_macro"] = _macro_f1(y_true, y_pred)
        primary = "accuracy"
    else:
        diffs = [float(a) - float(b) for a, b in zip(y_true, y_pred)]
        mae = sum(abs(d) for d in diffs) / n if n else 0.0
        mse = sum(d * d for d in diffs) / n if n else 0.0
        metrics_out["mae"] = mae
        metrics_out["mse"] = mse
        metrics_out["rmse"] = mse ** 0.5
        primary = "rmse"

    return {
        "primary_metric": primary,
        "primary_metric_value": metrics_out.get(primary),
        "metrics": metrics_out,
        "calibration_error": None,
        "evaluation_sample_size": n,
        "metric_suite_tool": "pure-python",
    }


def _macro_f1(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
    """Compute macro-averaged F1 with no external dependencies."""
    labels = sorted({*y_true, *y_pred})
    if not labels:
        return 0.0
    f1s: list[float] = []
    for lab in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == lab and b == lab)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != lab and b == lab)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == lab and b != lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def _empty_result(task: str) -> dict[str, Any]:
    """Return an empty metric-suite result stub."""
    primary = _DEFAULT_PRIMARY.get(task, "accuracy")
    return {
        "primary_metric": primary,
        "primary_metric_value": None,
        "metrics": {},
        "calibration_error": None,
        "evaluation_sample_size": 0,
        "metric_suite_tool": None,
    }
