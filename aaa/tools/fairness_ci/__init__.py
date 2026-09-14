"""fairness_ci — the precision of a fairness number, and the decision it supports.

Wilson / Newcombe intervals for proportions and their differences, Katz's log
interval for a ratio, pairwise decisions at a Bonferroni-adjusted level against
the four-fifths comparator, and one entry point that attaches the interval, the
cohort denominators and the verdict to the four metric families.

Usage
-----
    from aaa.tools.fairness_ci import annotate_metrics

    annotate_metrics(dp, eo, di, sg, y_true=y_true, y_pred=y_pred,
                     labels=resolution.labels, positive_label=1)
"""
from aaa.tools.fairness_ci.annotate import annotate_metrics  # noqa: F401
from aaa.tools.fairness_ci.decision import difference_decision, ratio_decision  # noqa: F401
from aaa.tools.fairness_ci.intervals import difference_ci, ratio_ci, wilson  # noqa: F401
from aaa.tools.fairness_ci.logger import CONFIDENCE_LEVEL, FOUR_FIFTHS, Z, logger  # noqa: F401
from aaa.tools.fairness_ci.pairs import adjusted_z  # noqa: F401
from aaa.tools.fairness_ci.stats import group_stats  # noqa: F401

__all__ = [
    'logger',
    'CONFIDENCE_LEVEL',
    'FOUR_FIFTHS',
    'Z',
    'wilson',
    'difference_ci',
    'ratio_ci',
    'adjusted_z',
    'difference_decision',
    'ratio_decision',
    'group_stats',
    'annotate_metrics',
]
