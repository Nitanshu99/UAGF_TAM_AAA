"""
equal_opportunity — Equal-opportunity fairness metric (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``equal_opportunity`` block.

Production path:  fairlearn ``MetricFrame`` with ``true_positive_rate``
                  and ``equalized_odds_difference``.
Offline/fallback: pure-Python TPR-per-group with no dependencies.

Usage
-----
    from src.tools.equal_opportunity import equal_opportunity

    result = equal_opportunity(
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

_DIFFERENCE_PASS_THRESHOLD = 0.10
_DIFFERENCE_OBSERVATION_THRESHOLD = 0.20


def equal_opportunity(
    y_true: Sequence[Any] | None = None,
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute equal-opportunity difference (max TPR gap across groups).

    Parameters
    ----------
    y_true, y_pred:
        Ground-truth + predicted labels.  Must be equal length.
    sensitive_features:
        Group label per prediction.  Must match y_pred length.
    positive_label:
        Value treated as the positive outcome.

    Returns
    -------
    dict matching the T12 ``equal_opportunity`` sub-schema:
        {
            metric, difference, tpr_by_group, verdict,
            sample_size, tool, positive_label
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
    """Use fairlearn for equal-opportunity computation."""
    from fairlearn.metrics import (  # type: ignore
        MetricFrame,
        true_positive_rate,
        equalized_odds_difference,
    )

    frame = MetricFrame(
        metrics=true_positive_rate,
        y_true=list(y_true),
        y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    )
    difference = float(equalized_odds_difference(
        y_true=list(y_true), y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    ))
    by_group = frame.by_group
    tpr_by_group = [
        {"group": str(g), "true_positive_rate": float(by_group.loc[g])}
        for g in by_group.index
    ]
    return {
        "metric": "equal_opportunity",
        "difference": difference,
        "tpr_by_group": tpr_by_group,
        "verdict": _band(difference),
        "sample_size": len(y_pred),
        "tool": "fairlearn",
        "positive_label": str(positive_label),
    }


# ---------------------------------------------------------------------------
# Pure-Python fallback
# ---------------------------------------------------------------------------

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
        positives = [(t, p) for t, p in pairs if t == positive_label]
        if not positives:
            tpr = 0.0
        else:
            tp = sum(1 for t, p in positives if p == positive_label)
            tpr = tp / len(positives)
        tpr_by_group.append({"group": g, "true_positive_rate": round(tpr, 6)})
        tprs.append(tpr)

    difference = (max(tprs) - min(tprs)) if len(tprs) >= 2 else 0.0
    return {
        "metric": "equal_opportunity",
        "difference": round(difference, 6),
        "tpr_by_group": tpr_by_group,
        "verdict": _band(difference),
        "sample_size": len(y_pred),
        "tool": "pure-python",
        "positive_label": str(positive_label),
    }


def _band(difference: float) -> str:
    """Map TPR-gap to PASS/PASS_WITH_OBSERVATIONS/FAIL band."""
    if difference <= _DIFFERENCE_PASS_THRESHOLD:
        return "PASS"
    if difference <= _DIFFERENCE_OBSERVATION_THRESHOLD:
        return "PASS_WITH_OBSERVATIONS"
    return "FAIL"


def _empty_result(positive_label: Any) -> dict[str, Any]:
    """Return an empty equal-opportunity result stub."""
    return {
        "metric": "equal_opportunity",
        "difference": None,
        "tpr_by_group": [],
        "verdict": "NOT_TESTED",
        "sample_size": 0,
        "tool": None,
        "positive_label": str(positive_label),
    }
