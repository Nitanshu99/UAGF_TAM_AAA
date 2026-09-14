"""Per-group counts behind every fairness metric, computed once per attribute."""
from __future__ import annotations

from typing import Any, Sequence


def group_stats(y_true: Sequence[Any] | None, y_pred: Sequence[Any],
                labels: Sequence[str], positive_label: Any) -> dict[str, dict[str, int]]:
    """Count everything the four metric families put in a denominator.

    :param y_true: Ground-truth labels (``None`` leaves the label-dependent
        counts at zero).
    :param y_pred: Predicted labels.
    :param labels: Resolved cohort label per prediction.
    :param positive_label: Value treated as the favourable outcome.
    :returns: ``{group: {n, selected, positives, true_positives, correct}}``.
    """
    truth = list(y_true) if y_true is not None else [None] * len(list(y_pred))
    out: dict[str, dict[str, int]] = {}
    for actual, pred, group in zip(truth, y_pred, labels):
        row = out.setdefault(str(group), {"n": 0, "selected": 0, "positives": 0,
                                          "true_positives": 0, "correct": 0})
        row["n"] += 1
        row["selected"] += int(pred == positive_label)
        row["correct"] += int(actual == pred)
        if actual == positive_label:
            row["positives"] += 1
            row["true_positives"] += int(pred == positive_label)
    return out


def counts_for(stats: dict[str, dict[str, int]], successes: str,
               trials: str) -> dict[str, tuple[int, int]]:
    """``{cohort: (successes, trials)}`` for one rate, from :func:`group_stats`.

    :param stats: Output of :func:`group_stats`.
    :param successes: Stats key holding the numerator.
    :param trials: Stats key holding the denominator.
    """
    return {group: (row[successes], row[trials]) for group, row in stats.items()}


__all__ = ["counts_for", "group_stats"]
