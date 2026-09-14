"""Every fairness number carries its precision, its denominators and its decision.

Fix 30 attached a 95 % interval and the group sizes to each metric, and left the
verdict to fixed bands on the point estimate — "the interval reports; it does not
gate". Case 05 (2026-09-14) showed what that costs: a ratio whose interval held
parity was read as below four-fifths. The interval now decides (see
:mod:`aaa.tools.fairness_ci.decision`):

* disparate impact — ``FAIL`` when a pair's ratio lies wholly below four-fifths,
  ``PASS`` when every pair's lies at or above it, ``INSUFFICIENT_EVIDENCE`` when
  the sample cannot tell;
* demographic parity, equal opportunity, subgroup accuracy — no regulatory
  tolerance exists for a difference, so an *established* difference (an interval
  excluding zero) is an observation and anything else passes.

The metric tools report the rates; the counts, intervals and verdicts are computed
here, once, from the same per-cohort counts.
"""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.fairness_ci.decision import difference_decision, ratio_decision
from aaa.tools.fairness_ci.pairs import Counts
from aaa.tools.fairness_ci.ratio_fields import apply_ratio
from aaa.tools.fairness_ci.record import interval
from aaa.tools.fairness_ci.stats import counts_for, group_stats


def _with_n(rows: list[dict[str, Any]], stats: dict[str, dict[str, int]],
            trials: str) -> None:
    """Put each cohort's denominator next to its rate, in place."""
    for row in rows:
        row["n"] = stats.get(str(row.get("group")), {}).get(trials, 0)


def _decide_difference(metric: dict[str, Any], counts: Counts) -> None:
    """An established difference is an observation; no established one passes."""
    if metric.get("sample_size") is None:  # the tool's own NOT_TESTED stub
        return
    found = difference_decision(counts)
    if found is None:
        metric["verdict"] = "NOT_TESTED"
        return
    metric["confidence_interval"] = interval(found, "newcombe")
    metric["verdict"] = "PASS_WITH_OBSERVATIONS" if found["established"] else "PASS"


def annotate_metrics(dp: dict[str, Any], eo: dict[str, Any], di: dict[str, Any],
                     sg: dict[str, Any], *, y_true: Sequence[Any] | None,
                     y_pred: Sequence[Any], labels: Sequence[str],
                     positive_label: Any, privileged_group: Any | None = None) -> None:
    """Attach interval, group sizes and verdict to each metric, in place.

    :param dp: ``demographic_parity`` result.
    :param eo: ``equal_opportunity`` result.
    :param di: ``disparate_impact`` result.
    :param sg: ``subgroup_metrics`` result.
    :param y_true: Ground-truth labels.
    :param y_pred: Predicted labels.
    :param labels: Resolved cohort label per prediction.
    :param positive_label: Value treated as the favourable outcome.
    :param privileged_group: The client's declared privileged cohort, if any.
    """
    stats = group_stats(y_true, y_pred, labels, positive_label)
    _with_n(dp.get("group_rates") or [], stats, "n")
    _with_n(eo.get("tpr_by_group") or [], stats, "positives")
    _decide_difference(dp, counts_for(stats, "selected", "n"))
    _decide_difference(eo, counts_for(stats, "true_positives", "positives"))
    _decide_difference(sg, counts_for(stats, "correct", "n"))
    if di.get("sample_size") is not None:
        found = ratio_decision(counts_for(stats, "selected", "n"),
                               None if privileged_group is None else str(privileged_group))
        apply_ratio(di, found, stats)


__all__ = ["annotate_metrics"]
