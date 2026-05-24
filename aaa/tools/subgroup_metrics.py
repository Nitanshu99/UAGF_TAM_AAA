"""
subgroup_metrics — Subgroup-performance breakdown (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``subgroup_metrics`` block.

Production path:  fairlearn ``MetricFrame`` with accuracy, selection_rate,
                  true_positive_rate, false_positive_rate per group.
Offline/fallback: pure-Python per-group metrics with no dependencies.

Usage
-----
    from src.tools.subgroup_metrics import subgroup_metrics

    result = subgroup_metrics(
        y_true=[1, 0, 1, 1, 0],
        y_pred=[1, 0, 0, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        positive_label=1,
    )
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

_ACCURACY_GAP_PASS_THRESHOLD = 0.10
_ACCURACY_GAP_OBSERVATION_THRESHOLD = 0.20


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


# ---------------------------------------------------------------------------
# fairlearn path
# ---------------------------------------------------------------------------

def _compute_fairlearn(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Use fairlearn MetricFrame for subgroup metrics."""
    from fairlearn.metrics import (  # type: ignore
        MetricFrame,
        selection_rate,
        true_positive_rate,
        false_positive_rate,
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
            "true_positive_rate": float(row["true_positive_rate"]),
            "false_positive_rate": float(row["false_positive_rate"]),
        })
    return _assemble(groups, len(y_pred), "fairlearn", positive_label)


# ---------------------------------------------------------------------------
# Pure-Python fallback
# ---------------------------------------------------------------------------

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
        tpr = (sum(1 for t, p in positives if p == positive_label) / len(positives)
               if positives else 0.0)
        fpr = (sum(1 for t, p in negatives if p == positive_label) / len(negatives)
               if negatives else 0.0)
        groups.append({
            "group": g,
            "size": n,
            "accuracy": round(correct / n, 6),
            "selection_rate": round(selected / n, 6),
            "true_positive_rate": round(tpr, 6),
            "false_positive_rate": round(fpr, 6),
        })
    return _assemble(groups, len(y_pred), "pure-python", positive_label)


def _assemble(
    groups: list[dict[str, Any]],
    sample_size: int,
    tool: str,
    positive_label: Any,
) -> dict[str, Any]:
    """Common assembly: derive accuracy gap, worst/best group, verdict."""
    if not groups:
        return _empty_result(positive_label)
    accs = [g["accuracy"] for g in groups]
    gap = (max(accs) - min(accs)) if len(accs) >= 2 else 0.0
    worst = min(groups, key=lambda r: r["accuracy"])["group"]
    best = max(groups, key=lambda r: r["accuracy"])["group"]
    if gap <= _ACCURACY_GAP_PASS_THRESHOLD:
        verdict = "PASS"
    elif gap <= _ACCURACY_GAP_OBSERVATION_THRESHOLD:
        verdict = "PASS_WITH_OBSERVATIONS"
    else:
        verdict = "FAIL"
    return {
        "metric": "subgroup_metrics",
        "groups": groups,
        "accuracy_gap": round(gap, 6),
        "worst_group": worst,
        "best_group": best,
        "verdict": verdict,
        "sample_size": sample_size,
        "tool": tool,
        "positive_label": str(positive_label),
    }


def _group_counts(sensitive_features: Sequence[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for g in sensitive_features:
        key = str(g)
        out[key] = out.get(key, 0) + 1
    return out


def _empty_result(positive_label: Any) -> dict[str, Any]:
    """Return an empty subgroup-metrics result stub."""
    return {
        "metric": "subgroup_metrics",
        "groups": [],
        "accuracy_gap": None,
        "worst_group": None,
        "best_group": None,
        "verdict": "NOT_TESTED",
        "sample_size": 0,
        "tool": None,
        "positive_label": str(positive_label),
    }
