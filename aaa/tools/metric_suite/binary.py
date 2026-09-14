"""Positive-class metrics for a binary target, and the headline metric they call for.

Every classifier was headlined by accuracy (``_DEFAULT_PRIMARY``). When the
positive class is the minority, accuracy rewards predicting the majority — case
03's 5 % anomaly detector would score 0.95 by never raising an alarm — so F1 on
the positive class is primary there (T-20260913-066). A provider's declared
``f1_score`` is scikit-learn's default, the positive-class F1, and was compared
with macro F1, a different quantity (T-20260913-069).
"""
from __future__ import annotations

from typing import Any, Sequence


def _is(value: Any, positive: Any) -> bool:
    """Label equality that tolerates ``1`` against ``"1"`` from a CSV."""
    return value == positive or str(value) == str(positive)


def _ratio(numerator: int, denominator: int) -> float | None:
    """A rate, or ``None`` when its denominator is empty — never a default 0."""
    return numerator / denominator if denominator else None


def binary_metrics(y_true: Sequence[Any], y_pred: Sequence[Any],
                   positive: Any) -> dict[str, float | None] | None:
    """Precision, recall, F1, FPR and FNR of the *positive* class.

    :returns: The metrics, or ``None`` when the labels are not binary or do not
        include *positive*.
    """
    labels = {str(v) for v in [*y_true, *y_pred] if v is not None}
    if len(labels) > 2 or str(positive) not in labels:
        return None
    pairs = [(_is(t, positive), _is(p, positive)) for t, p in zip(y_true, y_pred)]
    tp = sum(1 for t, p in pairs if t and p)
    fp = sum(1 for t, p in pairs if p and not t)
    fn = sum(1 for t, p in pairs if t and not p)
    tn = len(pairs) - tp - fp - fn
    return {"precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn),
            "f1": _ratio(2 * tp, 2 * tp + fp + fn), "fpr": _ratio(fp, fp + tn),
            "fnr": _ratio(fn, fn + tp)}


def apply_binary(result: dict[str, Any], y_true: Sequence[Any], y_pred: Sequence[Any],
                 positive: Any) -> None:
    """Add positive-class metrics to *result* and headline F1 when positives are the minority.

    :param result: A ``metric_suite`` result, updated in place.
    """
    metrics = binary_metrics(y_true, y_pred, positive)
    if metrics is None:
        return
    result["metrics"].update(metrics)
    pairs = [(_is(t, positive), _is(p, positive)) for t, p in zip(y_true, y_pred)]
    result["confusion"] = {"tp": sum(t and p for t, p in pairs), "fp": sum(p and not t for t, p in pairs),
                           "fn": sum(t and not p for t, p in pairs),
                           "tn": sum(not t and not p for t, p in pairs)}
    prevalence = sum(1 for t in y_true if _is(t, positive)) / len(y_true)
    if prevalence < 0.5 and metrics["f1"] is not None:
        result["primary_metric"], result["primary_metric_value"] = "f1", metrics["f1"]
