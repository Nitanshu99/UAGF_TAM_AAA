"""The fairness section's rows: per-attribute results, intervals and group counts."""
from __future__ import annotations

from typing import Any

from aaa.tools.report_render.numbers import fmt


def fairness_rows(t12: dict[str, Any]) -> list[tuple[str, str]]:
    """Per-metric fairness results from T12, with the group counts behind them."""
    if not t12:
        return []
    rows: list[tuple[str, str]] = [
        ("Verdict", str(t12.get("overall_fairness_verdict") or "—")),
        ("Sensitive features", ", ".join(t12.get("sensitive_features") or []) or "—"),
        ("Evaluation sample", str(t12.get("evaluation_sample_size") or "—")),
    ]
    for key, label in (("disparate_impact", "Disparate impact"),
                       ("demographic_parity", "Demographic parity"),
                       ("equal_opportunity", "Equal opportunity")):
        metric = t12.get(key) or {}
        if not metric:
            continue
        value = metric.get("ratio") if key == "disparate_impact" else metric.get("difference")
        groups = metric.get("group_rates") or metric.get("tpr_by_group") or []
        detail = f"{fmt(value)}  ({metric.get('verdict', '—')})"
        if groups:
            detail += f", over {len(groups)} group(s)"
        detail += _interval(metric)
        rows.append((label, detail))
    return rows + _grouping_rows(t12)
def _interval(metric: dict[str, Any]) -> str:
    """The 95 % interval beside the metric it qualifies (fix 30)."""
    interval = metric.get("confidence_interval") or {}
    low, high = interval.get("low"), interval.get("high")
    if low is None or high is None:
        return ""
    level = int(float(interval.get("level", 0.95)) * 100)
    return f", {level}% CI {fmt(low)}–{fmt(high)}"
def _grouping_rows(t12: dict[str, Any]) -> list[tuple[str, str]]:
    """The cohorts behind each attribute — including the ones never tested (fix 27).

    Without this a reader sees ``Demographic parity — (NOT_TESTED)`` and no
    reason. The smallest cohort is printed for every attribute, because it is what
    bounds how precisely the attribute's disparity could be placed.
    """
    rows: list[tuple[str, str]] = []
    for res in t12.get("group_resolution") or []:
        cohorts = f"{res.get('group_count', 0)} cohort(s)"
        if res.get("binned"):
            cohorts = f"{res.get('group_count', 0)} binned cohort(s)"
        state = ("tested" if res.get("tested")
                 else "not tested: fewer than two cohorts to compare")
        rows.append((f"Cohorts · {res.get('attribute', '?')}",
                     f"{cohorts}, smallest n={res.get('smallest_group_size', 0)} — {state}"))
    return rows


__all__ = ["_grouping_rows", "_interval", "fairness_rows"]
