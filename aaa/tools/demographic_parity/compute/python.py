"""Part 3 of the former ``demographic_parity`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.demographic_parity.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.demographic_parity.logger import logger  # noqa: F401


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

    # One group has no parity to measure, and no group selected has no ratio:
    # 0.0 and 1.0 stood in for both and read as measurements.
    difference = max(rates) - min(rates) if len(rates) >= 2 else None
    ratio = min(rates) / max(rates) if len(rates) >= 2 and max(rates) else None

    return {
        "metric": "demographic_parity",
        "difference": None if difference is None else round(difference, 6),
        "ratio": None if ratio is None else round(ratio, 6),
        "group_rates": group_rates,
        "sample_size": len(y_pred),
        "tool": "pure-python",
        "positive_label": str(positive_label),
    }
