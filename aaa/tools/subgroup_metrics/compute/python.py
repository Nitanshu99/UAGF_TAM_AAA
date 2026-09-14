"""Part 4 of the former ``subgroup_metrics`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.subgroup_metrics.assemble import _assemble, _group_counts  # noqa: F401
from aaa.tools.subgroup_metrics.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.subgroup_metrics.logger import _empty_result, logger  # noqa: F401


def _compute_python(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Pure-Python per-group accuracy, selection rate, TPR, FPR."""
    buckets: dict[str, list[tuple[Any, Any]]] = {}
    for t, p, g in zip(y_true, y_pred, sensitive_features):
        buckets.setdefault(str(g), []).append((t, p))

    groups: list[dict[str, Any]] = []
    for g, pairs in buckets.items():
        n = len(pairs)
        if n == 0:
            continue
        correct = sum(1 for t, p in pairs if t == p)
        selected = sum(1 for t, p in pairs if p == positive_label)
        positives = [(t, p) for t, p in pairs if t == positive_label]
        negatives = [(t, p) for t, p in pairs if t != positive_label]
        # No positives (negatives) means no TPR (FPR) — not a rate of 0.0.
        tpr = (sum(1 for t, p in positives if p == positive_label) / len(positives)
               if positives else None)
        fpr = (sum(1 for t, p in negatives if p == positive_label) / len(negatives)
               if negatives else None)
        groups.append({
            "group": g,
            "size": n,
            "accuracy": round(correct / n, 6),
            "selection_rate": round(selected / n, 6),
            "true_positive_rate": None if tpr is None else round(tpr, 6),
            "false_positive_rate": None if fpr is None else round(fpr, 6),
        })
    return _assemble(groups, len(y_pred), "pure-python", positive_label)
