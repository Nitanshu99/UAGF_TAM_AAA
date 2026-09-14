"""Part 2 of the former ``equal_opportunity`` module (auto-split)."""
from __future__ import annotations

from math import isnan
from typing import Any, Sequence

from aaa.tools.equal_opportunity.logger import logger  # noqa: F401


def _compute_fairlearn(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    sensitive_features: Sequence[Any],
    positive_label: Any,
) -> dict[str, Any]:
    """Use fairlearn for equal-opportunity computation."""
    from fairlearn.metrics import MetricFrame, true_positive_rate  # type: ignore

    frame = MetricFrame(
        metrics=true_positive_rate,
        y_true=list(y_true),
        y_pred=list(y_pred),
        sensitive_features=list(sensitive_features),
    )
    # The TPR gap itself. ``equalized_odds_difference`` — used here before — is the
    # larger of the TPR *and FPR* gaps, so a false-positive disparity was reported
    # as unequal opportunity. A group with no positives has no rate (NaN), not 0.
    by_group = frame.by_group
    rates = {str(g): float(by_group.loc[g]) for g in by_group.index}
    tpr_by_group = [{"group": g, "true_positive_rate": None if isnan(r) else r}
                    for g, r in rates.items()]
    defined = [r for r in rates.values() if not isnan(r)]
    difference = max(defined) - min(defined) if len(defined) >= 2 else None
    return {
        "metric": "equal_opportunity",
        "difference": difference,
        "tpr_by_group": tpr_by_group,
        "sample_size": len(y_pred),
        "tool": "fairlearn",
        "positive_label": str(positive_label),
    }
