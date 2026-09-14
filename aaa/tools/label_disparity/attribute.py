"""Positive-label rate by group for one protected attribute, and what it decides."""
from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

from aaa.tools.fairness_ci import CONFIDENCE_LEVEL, FOUR_FIFTHS, ratio_decision
from aaa.tools.fairness_groups import is_continuous, resolve_groups


def group_labels(attribute: str, values: Sequence[Any]) -> list[str]:
    """Group labels: quantile bands for a continuous attribute, the value otherwise."""
    return resolve_groups(attribute, values).labels if is_continuous(values) else [
        str(v) for v in values]


def attribute_disparity(attribute: str, values: Sequence[Any],
                        positive: Sequence[bool]) -> dict[str, Any]:
    """Every group's positive-label rate, and the four-fifths question decided by interval.

    Groups under thirty rows were excluded, and the point ratio was compared with 0.8.
    Case 05 then read 0.748 over groups of 71 and 88 — an interval of about 0.55 to
    1.02 — as below four-fifths. Every group is now kept, and the ratio decides only
    where its interval does (:func:`aaa.tools.fairness_ci.ratio_decision`).

    :param attribute: Column name.
    :param values: Its values, row-aligned with *positive* (missing values removed).
    :param positive: Whether each row carries the positive label.
    """
    labels = group_labels(attribute, values)
    counts = {group: (sum(p for label, p in zip(labels, positive) if label == group), n)
              for group, n in Counter(labels).items()}
    groups = [{"group": g, "n": n, "positive_rate": round(k / n, 4)}
              for g, (k, n) in sorted(counts.items(), key=lambda kv: (-kv[1][1], kv[0]))]
    found = ratio_decision(counts)
    result: dict[str, Any] = {"attribute": attribute, "groups": groups, "lowest_group": None,
                              "highest_group": None, "ratio": None, "ratio_interval": None,
                              "four_fifths_passed": None}
    if found is None:
        return {**result, "tested": False, "reason": (
            "fewer than two groups" if len(counts) < 2 else "no group carries the positive label")}
    low, high = found["interval"]
    return {**result, "tested": True, "reason": _decided(found["decision"], low, high),
            "lowest_group": found["group"],
            "highest_group": found["baseline"], "ratio": round(found["ratio"], 4),
            "ratio_interval": {"low": round(low, 4), "high": round(high, 4),
                               "level": CONFIDENCE_LEVEL, "comparisons": found["comparisons"],
                               "method": "katz-log; Bonferroni-adjusted over every pair"},
            "four_fifths_passed": {"adverse": False, "within": True}.get(found["decision"])}


def _decided(decision: str, low: float, high: float) -> str:
    """What the interval decides, in words: an undecided null is not an unexplained one."""
    span = f"the ratio's interval {low:.4f}–{high:.4f}"
    return {"adverse": f"adverse impact established: {span} lies wholly below {FOUR_FIFTHS}",
            "within": f"within the four-fifths ratio: every pair's interval lies at or above {FOUR_FIFTHS}",
            }.get(decision, f"undecided: {span} spans {FOUR_FIFTHS}, so this sample establishes "
                            "neither adverse impact nor its absence")


__all__ = ["FOUR_FIFTHS", "attribute_disparity", "group_labels"]
