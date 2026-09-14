"""Part 3 of the former ``equal_opportunity`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.equal_opportunity.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.equal_opportunity.logger import logger  # noqa: F401


def _compute_python(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Pure-Python TPR per group."""
    groups: dict[str, list[tuple[Any, Any]]] = {}
    for t, p, g in zip(y_true, y_pred, sensitive_features):
        groups.setdefault(str(g), []).append((t, p))

    tpr_by_group: list[dict[str, Any]] = []
    tprs: list[float] = []
    for g, pairs in groups.items():
        positives = [p for t, p in pairs if t == positive_label]
        # A group with no positives has no true-positive rate; 0.0 ranked it lowest.
        tpr = sum(1 for p in positives if p == positive_label) / len(positives) if positives else None
        tpr_by_group.append({"group": g, "true_positive_rate": None if tpr is None else round(tpr, 6)})
        tprs.extend([] if tpr is None else [tpr])

    difference = (max(tprs) - min(tprs)) if len(tprs) >= 2 else None
    return {
        "metric": "equal_opportunity",
        "difference": None if difference is None else round(difference, 6),
        "tpr_by_group": tpr_by_group,
        "sample_size": len(y_pred),
        "tool": "pure-python",
        "positive_label": str(positive_label),
    }


def _empty_result(positive_label: Any) -> dict[str, Any]:
    """Return an empty equal-opportunity result stub."""
    return {
        "metric": "equal_opportunity",
        "difference": None,
        "tpr_by_group": [],
        "verdict": "NOT_TESTED",
        # Not computed: no sample, rather than a sample of zero (T-20260913-033).
        "sample_size": None,
        "tool": None,
        "positive_label": str(positive_label),
    }
