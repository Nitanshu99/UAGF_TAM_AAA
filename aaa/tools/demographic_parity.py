"""
demographic_parity — Demographic-parity fairness metric (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``demographic_parity`` block.

Production path:  fairlearn ``MetricFrame`` / ``demographic_parity_difference``
                  and ``demographic_parity_ratio``.
Offline/fallback: pure-Python selection-rate per group with no dependencies.

Usage
-----
    from src.tools.demographic_parity import demographic_parity

    result = demographic_parity(
        y_pred=[1, 0, 1, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        positive_label=1,
    )
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

# Bands consistent with EEOC "four-fifths" rule and fairlearn defaults.
_RATIO_PASS_THRESHOLD = 0.80
_DIFFERENCE_PASS_THRESHOLD = 0.10


def demographic_parity(
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute demographic-parity difference and ratio.

    Parameters
    ----------
    y_pred:
        Predicted labels.  Empty / None → returns an empty-result stub.
    sensitive_features:
        Group label per prediction (e.g. ``"M"``/``"F"``).  Must be the
        same length as ``y_pred``.
    positive_label:
        Value treated as the positive outcome when computing selection rate.

    Returns
    -------
    dict matching the T12 ``demographic_parity`` sub-schema:
        {
            metric, difference, ratio, group_rates,
            verdict, sample_size, tool, positive_label
        }
    """
    if (y_pred is None or sensitive_features is None
            or len(y_pred) == 0 or len(sensitive_features) == 0
            or len(y_pred) != len(sensitive_features)):
        return _empty_result(positive_label)

    try:
        return _compute_fairlearn(y_pred, sensitive_features, positive_label)
    except Exception as exc:
        logger.info("fairlearn unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_pred, sensitive_features, positive_label)


# ---------------------------------------------------------------------------
# fairlearn path
# ---------------------------------------------------------------------------

def _compute_fairlearn(
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Use fairlearn for demographic-parity computation."""
    from fairlearn.metrics import (  # type: ignore
        MetricFrame,
        demographic_parity_difference,
        demographic_parity_ratio,
        selection_rate,
    )

    y_true_stub = list(y_pred)  # selection_rate ignores y_true; pass placeholder
    frame = MetricFrame(
        metrics=selection_rate,
        y_true=y_true_stub,
        y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    )
    difference = float(demographic_parity_difference(
        y_true=y_true_stub, y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    ))
    ratio = float(demographic_parity_ratio(
        y_true=y_true_stub, y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    ))
    by_group = frame.by_group
    group_rates = [
        {"group": str(g), "selection_rate": float(by_group.loc[g])}
        for g in by_group.index
    ]
    verdict = _band(difference, ratio)
    return {
        "metric": "demographic_parity",
        "difference": difference,
        "ratio": ratio,
        "group_rates": group_rates,
        "verdict": verdict,
        "sample_size": len(y_pred),
        "tool": "fairlearn",
        "positive_label": str(positive_label),
    }


# ---------------------------------------------------------------------------
# Pure-Python fallback
# ---------------------------------------------------------------------------

def _compute_python(
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Pure-Python selection-rate per group."""
    groups: dict[str, list[Any]] = {}
    for p, g in zip(y_pred, sensitive_features):
        groups.setdefault(str(g), []).append(p)

    group_rates = []
    rates: list[float] = []
    for g, preds in groups.items():
        rate = sum(1 for v in preds if v == positive_label) / len(preds) if preds else 0.0
        group_rates.append({"group": g, "selection_rate": round(rate, 6)})
        rates.append(rate)

    if len(rates) < 2:
        difference = 0.0
        ratio = 1.0
    else:
        difference = max(rates) - min(rates)
        ratio = (min(rates) / max(rates)) if max(rates) else 0.0

    return {
        "metric": "demographic_parity",
        "difference": round(difference, 6),
        "ratio": round(ratio, 6),
        "group_rates": group_rates,
        "verdict": _band(difference, ratio),
        "sample_size": len(y_pred),
        "tool": "pure-python",
        "positive_label": str(positive_label),
    }


def _band(difference: float, ratio: float) -> str:
    """Map difference/ratio to PASS/PASS_WITH_OBSERVATIONS/FAIL band."""
    if ratio >= _RATIO_PASS_THRESHOLD and difference <= _DIFFERENCE_PASS_THRESHOLD:
        return "PASS"
    if ratio >= 0.60 and difference <= 0.20:
        return "PASS_WITH_OBSERVATIONS"
    return "FAIL"


def _empty_result(positive_label: Any) -> dict[str, Any]:
    """Return an empty demographic-parity result stub."""
    return {
        "metric": "demographic_parity",
        "difference": None,
        "ratio": None,
        "group_rates": [],
        "verdict": "NOT_TESTED",
        "sample_size": 0,
        "tool": None,
        "positive_label": str(positive_label),
    }
