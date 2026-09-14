"""Part 5 of the former ``metric_suite`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.metric_suite.binary import apply_binary
from aaa.tools.metric_suite.compute.python import _compute_python, _empty_result  # noqa: F401
from aaa.tools.metric_suite.compute.sklearn import _compute_sklearn  # noqa: F401
from aaa.tools.metric_suite.logger import (  # noqa: F401
    _DEFAULT_PRIMARY,
    _sklearn_classification,
    logger,
)
from aaa.tools.metric_suite.macro_f1 import _macro_f1  # noqa: F401


def metric_suite(
    y_true: Sequence[Any] | None = None,
    y_pred: Sequence[Any] | None = None,
    y_proba: Sequence[Any] | None = None,
    task: str = "classification",
    positive_label: Any = None,
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
    positive_label:
        The favourable/detected class of a binary target. When given, the
        positive-class precision, recall, F1, FPR and FNR are added, and F1 is
        the primary metric if that class is the minority (:mod:`.binary`).

    Returns
    -------
    dict matching the T09 ``performance_metrics`` sub-schema:
        {
            primary_metric, primary_metric_value, metrics,
            calibration_error, evaluation_sample_size, metric_suite_tool
        }
    """
    if y_true is None or y_pred is None or len(y_true) == 0 or len(y_pred) == 0:
        return _empty_result()

    try:
        result = _compute_sklearn(y_true, y_pred, y_proba, task)
    except Exception as exc:
        logger.info("scikit-learn unavailable (%s); using pure-Python fallback.", exc)
        result = _compute_python(y_true, y_pred, y_proba, task)
    if task == "classification" and positive_label is not None:
        apply_binary(result, y_true, y_pred, positive_label)
    return result
