"""A metric's 95% bootstrap interval on the evaluation set it was measured on.

Whether a provider's declared accuracy is corroborated depends on how precisely the
audit measured it: a 0.02 gap is noise on 80 rows and a discrepancy on 80,000. The
percentile bootstrap resamples the evaluation rows and recomputes the metric each
time (Efron & Tibshirani, 1993, recommend at least 1,000 resamples for percentile
intervals); its seed is fixed so a rerun reproduces the interval (T-20260914-002).
"""
from __future__ import annotations

from typing import Any, Sequence

#: Resamples, confidence level and seed of the interval.
ROUNDS, LEVEL, SEED = 1000, 0.95, 123


def _resampled(name: str, true_pos: Any, pred_pos: Any, agree: Any, idx: Any) -> Any:
    """The metric recomputed on every resample (rows of *idx*), NaN where undefined."""
    import numpy as np  # type: ignore

    if name == "accuracy":
        return agree[idx].mean(axis=1)
    tp = (true_pos[idx] & pred_pos[idx]).sum(axis=1).astype(float)
    fp = (~true_pos[idx] & pred_pos[idx]).sum(axis=1)
    fn = (true_pos[idx] & ~pred_pos[idx]).sum(axis=1)
    denominator = {"precision": tp + fp, "recall": tp + fn, "f1": 2 * tp + fp + fn}[name]
    numerator = 2 * tp if name == "f1" else tp
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(denominator > 0, numerator / np.maximum(denominator, 1), np.nan)


def _auc(true_pos: Any, scores: Any, idx: Any) -> Any:
    """ROC AUC on every resample that holds both classes."""
    import numpy as np  # type: ignore
    from sklearn.metrics import roc_auc_score  # type: ignore

    return np.array([roc_auc_score(true_pos[i], scores[i]) if 0 < true_pos[i].sum() < len(i)
                     else np.nan for i in idx])


def bootstrap_intervals(y_true: Sequence[Any], y_pred: Sequence[Any],
                        y_proba: Sequence[Any] | None, positive: Any,
                        names: Sequence[str]) -> dict[str, tuple[float, float]]:
    """95% percentile intervals of *names* (accuracy, precision, recall, f1, roc_auc).

    :param positive: The positive label; without it only accuracy has an interval.
    :returns: ``{metric: (low, high)}`` for each metric that is defined on the data.
    """
    import numpy as np  # type: ignore

    if not y_true or len(y_true) != len(y_pred):
        return {}
    truth, pred = np.array([str(v) for v in y_true]), np.array([str(v) for v in y_pred])
    idx = np.random.default_rng(SEED).integers(0, len(truth), size=(ROUNDS, len(truth)))
    true_pos, pred_pos = truth == str(positive), pred == str(positive)
    out: dict[str, tuple[float, float]] = {}
    for name in names:
        if name == "roc_auc":
            if positive is None or y_proba is None or len(y_proba) != len(truth):
                continue
            # The score is the upper class's probability, as the measured AUC used it.
            upper = np.asarray(y_true) == np.unique(np.asarray(y_true))[-1]
            values = _auc(upper, np.asarray(y_proba, dtype=float), idx)
        elif name == "accuracy" or positive is not None:
            values = _resampled(name, true_pos, pred_pos, truth == pred, idx)
        else:
            continue
        values = values[~np.isnan(values)]
        if len(values):
            tail = (1 - LEVEL) / 2 * 100
            out[name] = (float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail)))
    return out


__all__ = ["LEVEL", "ROUNDS", "SEED", "bootstrap_intervals"]
