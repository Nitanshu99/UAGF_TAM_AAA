"""Part 5 of the former ``subgroup_metrics`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.subgroup_metrics.assemble import _assemble, _group_counts  # noqa: F401
from aaa.tools.subgroup_metrics.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.subgroup_metrics.compute.python import _compute_python  # noqa: F401
from aaa.tools.subgroup_metrics.logger import _empty_result, logger  # noqa: F401


def subgroup_metrics(
    y_true: Sequence[Any] | None = None,
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute per-group accuracy, selection rate, TPR, and FPR.

    Returns
    -------
    dict matching the T12 ``subgroup_metrics`` sub-schema:
        {
            groups[], accuracy_gap, worst_group, best_group,
            verdict, sample_size, tool, positive_label
        }
    """
    if (y_true is None or y_pred is None or sensitive_features is None
            or len(y_true) == 0 or len(y_pred) == 0
            or len(y_true) != len(y_pred)
            or len(y_pred) != len(sensitive_features)):
        return _empty_result(positive_label)

    try:
        return _compute_fairlearn(y_true, y_pred, sensitive_features, positive_label)
    except Exception as exc:
        logger.info("fairlearn unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_true, y_pred, sensitive_features, positive_label)
