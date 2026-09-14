"""subgroup_metrics — Subgroup-performance breakdown (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``subgroup_metrics`` block.

Production path:  fairlearn ``MetricFrame`` with accuracy, selection_rate,
                  true_positive_rate, false_positive_rate per group.
Fallback: pure-Python per-group metrics with no dependencies.

Usage
-----
    from src.tools.subgroup_metrics import subgroup_metrics

    result = subgroup_metrics(
        y_true=[1, 0, 1, 1, 0],
        y_pred=[1, 0, 0, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        positive_label=1,
    )"""
from aaa.tools.subgroup_metrics.assemble import _assemble, _group_counts  # noqa: F401
from aaa.tools.subgroup_metrics.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.subgroup_metrics.compute.python import _compute_python  # noqa: F401
from aaa.tools.subgroup_metrics.core import subgroup_metrics  # noqa: F401
from aaa.tools.subgroup_metrics.logger import _empty_result, logger  # noqa: F401

__all__ = [
    'logger',
    '_empty_result',
    '_assemble',
    '_group_counts',
    '_compute_fairlearn',
    '_compute_python',
    'subgroup_metrics',
]
