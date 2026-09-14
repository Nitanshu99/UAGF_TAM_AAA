"""Part 3 of the former ``subgroup_metrics`` module (auto-split)."""
from __future__ import annotations

from math import isnan
from typing import Any, Sequence

from aaa.tools.subgroup_metrics.assemble import _assemble, _group_counts  # noqa: F401
from aaa.tools.subgroup_metrics.logger import _empty_result, logger  # noqa: F401


def _rate(value: Any) -> float | None:
    """A per-group rate, or ``None`` where the group had nothing to divide by."""
    return None if isnan(float(value)) else float(value)


def _compute_fairlearn(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Use fairlearn MetricFrame for subgroup metrics."""
    from fairlearn.metrics import (  # type: ignore
        MetricFrame,
        false_positive_rate,
        selection_rate,
        true_positive_rate,
    )
    from sklearn.metrics import accuracy_score  # type: ignore

    frame = MetricFrame(
        metrics={
            "accuracy": accuracy_score,
            "selection_rate": selection_rate,
            "true_positive_rate": true_positive_rate,
            "false_positive_rate": false_positive_rate,
        },
        y_true=list(y_true),
        y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    )
    by_group = frame.by_group
    counts = _group_counts(sensitive_features)
    groups: list[dict[str, Any]] = []
    for g in by_group.index:
        row = by_group.loc[g]
        groups.append({
            "group": str(g),
            "size": counts.get(str(g), 0),
            "accuracy": float(row["accuracy"]),
            "selection_rate": float(row["selection_rate"]),
            "true_positive_rate": _rate(row["true_positive_rate"]),
            "false_positive_rate": _rate(row["false_positive_rate"]),
        })
    return _assemble(groups, len(y_pred), "fairlearn", positive_label)
