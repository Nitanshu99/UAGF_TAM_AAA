"""disparate_impact — Disparate-impact fairness metric (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``disparate_impact`` block.

Production path:  IBM AIF360 ``BinaryLabelDatasetMetric.disparate_impact``.
Offline/fallback: pure-Python four-fifths-rule ratio with no dependencies.

Usage
-----
    from src.tools.disparate_impact import disparate_impact

    result = disparate_impact(
        y_pred=[1, 0, 1, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        privileged_group="M",
        positive_label=1,
    )"""
from aaa.tools.disparate_impact.compute.aif360 import _compute_aif360  # noqa: F401
from aaa.tools.disparate_impact.compute.python import _compute_python  # noqa: F401
from aaa.tools.disparate_impact.core import disparate_impact  # noqa: F401
from aaa.tools.disparate_impact.empty_result import _empty_result  # noqa: F401
from aaa.tools.disparate_impact.logger import _assemble_result, logger  # noqa: F401

__all__ = [
    'logger',
    '_assemble_result',
    '_compute_aif360',
    '_empty_result',
    '_compute_python',
    'disparate_impact',
]
