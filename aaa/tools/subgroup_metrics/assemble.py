"""Part 2 of the former ``subgroup_metrics`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.subgroup_metrics.logger import _empty_result, logger  # noqa: F401


def _assemble(
    groups: list[dict[str, Any]],
    sample_size: int,
    tool: str,
    positive_label: Any,
) -> dict[str, Any]:
    """Common assembly: accuracy gap and worst/best group (the verdict is the suite's)."""
    if not groups:
        return _empty_result(positive_label)
    accs = [g["accuracy"] for g in groups]
    gap = (max(accs) - min(accs)) if len(accs) >= 2 else None
    worst = min(groups, key=lambda r: r["accuracy"])["group"]
    best = max(groups, key=lambda r: r["accuracy"])["group"]
    return {
        "metric": "subgroup_metrics",
        "groups": groups,
        "accuracy_gap": None if gap is None else round(gap, 6),
        "worst_group": worst,
        "best_group": best,
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
