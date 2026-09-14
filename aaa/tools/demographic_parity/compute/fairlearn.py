"""Part 2 of the former ``demographic_parity`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.demographic_parity.logger import logger  # noqa: F401


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
    return {
        "metric": "demographic_parity",
        "difference": difference,
        "ratio": ratio,
        "group_rates": group_rates,
        "sample_size": len(y_pred),
        "tool": "fairlearn",
        "positive_label": str(positive_label),
    }
