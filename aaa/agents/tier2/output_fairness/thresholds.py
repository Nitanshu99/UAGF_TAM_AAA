"""Reading a fairness metric against its threshold, and the confidence interval behind it."""
from __future__ import annotations

from typing import Any

from aaa.tools.report_render.numbers import fmt


def _over(res: dict[str, Any]) -> str:
    """The cohorts a disparity was measured over, for the finding's own text."""
    if not res.get("group_count"):
        return ""
    band = " binned" if res.get("binned") else ""
    return (f", over {res['group_count']}{band} group(s), "
            f"smallest n={res['smallest_group_size']}")
def _ci(metric: dict[str, Any]) -> str:
    """The interval beside the number it qualifies (fix 30).

    A ratio of 0.660 whose interval spans 1.0 has not established a disparity,
    and the sentence that asserts one has to say so in the same breath.
    """
    interval = metric.get("confidence_interval") or {}
    low, high = interval.get("low"), interval.get("high")
    if low is None or high is None:
        return ""
    level = int(float(interval.get("level", 0.95)) * 100)
    groups = interval.get("groups") or []
    pair = f", {groups[0]} vs {groups[1]}" if len(groups) == 2 else ""
    many = interval.get("comparisons") or 1
    adjusted = f", adjusted for {many} pairwise comparisons" if many > 1 else ""
    return f" [{level}% CI {fmt(low)}–{fmt(high)}{pair}{adjusted}]"


__all__ = ["_ci", "_over"]
