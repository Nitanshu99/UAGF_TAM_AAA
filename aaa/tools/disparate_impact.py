"""
disparate_impact — Disparate-impact fairness metric (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``disparate_impact`` block.

Production path:  IBM AIF360 ``BinaryLabelDatasetMetric.disparate_impact``.
Offline/fallback: pure-Python four-fifths-rule ratio with no dependencies.

Usage
-----
    from src.tools.disparate_impact import disparate_impact

    result = disparate_impact(
        y_pred=[1, 0, 1, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        privileged_group="M",
        positive_label=1,
    )
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

# Four-fifths rule (EEOC 1978): ratio < 0.80 = adverse impact.
_FOUR_FIFTHS_THRESHOLD = 0.80
_OBSERVATION_THRESHOLD = 0.60


def disparate_impact(
    y_pred: Sequence[Any] | None = None,
    sensitive_features: Sequence[Any] | None = None,
    privileged_group: Any | None = None,
    positive_label: Any = 1,
) -> dict[str, Any]:
    """
    Compute disparate-impact ratio (unprivileged_selection / privileged_selection).

    Parameters
    ----------
    y_pred:
        Predicted labels.
    sensitive_features:
        Group label per prediction.
    privileged_group:
        Label of the privileged group.  If ``None`` the most-selected group
        is treated as privileged (heuristic).
    positive_label:
        Value treated as the positive outcome.

    Returns
    -------
    dict matching the T12 ``disparate_impact`` sub-schema:
        {
            metric, ratio, privileged_group, unprivileged_group,
            privileged_selection_rate, unprivileged_selection_rate,
            four_fifths_rule_passed, verdict,
            sample_size, tool, positive_label
        }
    """
    if (y_pred is None or sensitive_features is None
            or len(y_pred) == 0 or len(sensitive_features) == 0
            or len(y_pred) != len(sensitive_features)):
        return _empty_result(privileged_group, positive_label)

    try:
        return _compute_aif360(y_pred, sensitive_features, privileged_group, positive_label)
    except Exception as exc:
        logger.info("aif360 unavailable (%s); using pure-Python fallback.", exc)
        return _compute_python(y_pred, sensitive_features, privileged_group, positive_label)


# ---------------------------------------------------------------------------
# aif360 path
# ---------------------------------------------------------------------------

def _compute_aif360(
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    privileged_group: Any | None,
    positive_label: Any,
) -> dict[str, Any]:
    """Use IBM AIF360 BinaryLabelDatasetMetric for disparate-impact."""
    import pandas as pd  # type: ignore
    from aif360.datasets import BinaryLabelDataset  # type: ignore
    from aif360.metrics import BinaryLabelDatasetMetric  # type: ignore

    groups = sorted({str(g) for g in sensitive_features})
    priv = str(privileged_group) if privileged_group is not None else groups[0]
    unpriv = [g for g in groups if g != priv][0] if len(groups) >= 2 else priv

    df = pd.DataFrame({
        "label": [1 if v == positive_label else 0 for v in y_pred],
        "group": [1 if str(g) == priv else 0 for g in sensitive_features],
    })
    bld = BinaryLabelDataset(
        df=df, label_names=["label"], protected_attribute_names=["group"],
        favorable_label=1, unfavorable_label=0,
    )
    metric = BinaryLabelDatasetMetric(
        bld,
        unprivileged_groups=[{"group": 0}],
        privileged_groups=[{"group": 1}],
    )
    ratio = float(metric.disparate_impact())
    priv_rate = float(metric.selection_rate(privileged=True))
    unpriv_rate = float(metric.selection_rate(privileged=False))
    return _assemble_result(
        ratio, priv, unpriv, priv_rate, unpriv_rate,
        len(y_pred), "aif360", positive_label,
    )


# ---------------------------------------------------------------------------
# Pure-Python fallback
# ---------------------------------------------------------------------------

def _compute_python(
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    privileged_group: Any | None,
    positive_label: Any,
) -> dict[str, Any]:
    """Pure-Python selection-rate ratio (four-fifths rule)."""
    rates: dict[str, float] = {}
    counts: dict[str, int] = {}
    for p, g in zip(y_pred, sensitive_features):
        key = str(g)
        counts[key] = counts.get(key, 0) + 1
        if p == positive_label:
            rates[key] = rates.get(key, 0.0) + 1.0
    for k in counts:
        rates[k] = rates.get(k, 0.0) / counts[k] if counts[k] else 0.0

    if not rates:
        return _empty_result(privileged_group, positive_label)

    if privileged_group is not None and str(privileged_group) in rates:
        priv = str(privileged_group)
    else:
        priv = max(rates, key=lambda k: rates[k])
    unpriv_candidates = [g for g in rates if g != priv]
    unpriv = unpriv_candidates[0] if unpriv_candidates else priv

    priv_rate = rates[priv]
    unpriv_rate = rates[unpriv]
    ratio = (unpriv_rate / priv_rate) if priv_rate else 0.0

    return _assemble_result(
        ratio, priv, unpriv, priv_rate, unpriv_rate,
        len(y_pred), "pure-python", positive_label,
    )


def _assemble_result(
    ratio: float,
    priv: str,
    unpriv: str,
    priv_rate: float,
    unpriv_rate: float,
    sample_size: int,
    tool: str,
    positive_label: Any,
) -> dict[str, Any]:
    """Common assembly for both aif360 and python paths."""
    four_fifths_passed = ratio >= _FOUR_FIFTHS_THRESHOLD
    if four_fifths_passed:
        verdict = "PASS"
    elif ratio >= _OBSERVATION_THRESHOLD:
        verdict = "PASS_WITH_OBSERVATIONS"
    else:
        verdict = "FAIL"
    return {
        "metric": "disparate_impact",
        "ratio": round(ratio, 6),
        "privileged_group": priv,
        "unprivileged_group": unpriv,
        "privileged_selection_rate": round(priv_rate, 6),
        "unprivileged_selection_rate": round(unpriv_rate, 6),
        "four_fifths_rule_passed": four_fifths_passed,
        "verdict": verdict,
        "sample_size": sample_size,
        "tool": tool,
        "positive_label": str(positive_label),
    }


def _empty_result(privileged_group: Any | None, positive_label: Any) -> dict[str, Any]:
    """Return an empty disparate-impact result stub."""
    return {
        "metric": "disparate_impact",
        "ratio": None,
        "privileged_group": str(privileged_group) if privileged_group is not None else None,
        "unprivileged_group": None,
        "privileged_selection_rate": None,
        "unprivileged_selection_rate": None,
        "four_fifths_rule_passed": None,
        "verdict": "NOT_TESTED",
        "sample_size": 0,
        "tool": None,
        "positive_label": str(positive_label),
    }
