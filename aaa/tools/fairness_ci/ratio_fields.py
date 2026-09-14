"""Writing a four-fifths decision into the ``disparate_impact`` result.

The ratio is a comparison of two named cohorts, so the cohorts, rates and sizes the
artefact prints must be the pair the decision rests on. When an adverse pair is not
the most- against least-selected one, the tool's pair is replaced by it.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.fairness_ci.record import interval

_VERDICT = {"adverse": "FAIL", "within": "PASS", "undecided": "INSUFFICIENT_EVIDENCE"}


def apply_ratio(di: dict[str, Any], found: dict[str, Any] | None,
                stats: dict[str, dict[str, int]]) -> None:
    """Set verdict, pair, rates and interval on *di* from *found*, in place.

    :param di: ``disparate_impact`` result.
    :param found: :func:`~aaa.tools.fairness_ci.decision.ratio_decision` output.
    :param stats: Per-cohort counts the decision was computed from.
    """
    if found is None:
        di.update(verdict="NOT_TESTED", ratio=None, four_fifths_rule_passed=None)
        return
    group, baseline = stats[found["group"]], stats[found["baseline"]]
    di.update(
        ratio=round(found["ratio"], 6), unprivileged_group=found["group"],
        privileged_group=found["baseline"],
        unprivileged_selection_rate=round(group["selected"] / group["n"], 6),
        privileged_selection_rate=round(baseline["selected"] / baseline["n"], 6),
        unprivileged_group_size=group["n"], privileged_group_size=baseline["n"],
        unprivileged_selected=group["selected"], privileged_selected=baseline["selected"],
        four_fifths_rule_passed={"adverse": False, "within": True}.get(found["decision"]),
        verdict=_VERDICT[found["decision"]],
        confidence_interval=interval(found, "katz-log"))


__all__ = ["apply_ratio"]
