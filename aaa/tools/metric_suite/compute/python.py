"""Part 4 of the former ``metric_suite`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.metric_suite.compute.sklearn import _compute_sklearn  # noqa: F401
from aaa.tools.metric_suite.logger import (  # noqa: F401
    _DEFAULT_PRIMARY,
    _sklearn_classification,
    logger,
)
from aaa.tools.metric_suite.macro_f1 import _macro_f1  # noqa: F401


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


def _empty_result() -> dict[str, Any]:
    """Return an empty metric-suite result stub.

    A primary metric is a property of an evaluation; with none run, naming the task's
    usual one ("accuracy") described a ranking system's model card as scored on
    accuracy — Phase 3 defaults an undeclared task to classification (live run bb7837).
    """
    return {
        "primary_metric": "not measured",
        "primary_metric_value": None,
        "metrics": {},
        "calibration_error": None,
        # Nothing was evaluated: unknown, not an evaluation of zero samples (F6).
        "evaluation_sample_size": None,
        "metric_suite_tool": None,
    }
