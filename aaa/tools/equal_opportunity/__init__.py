"""equal_opportunity — Equal-opportunity fairness metric (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``equal_opportunity`` block.

Production path:  fairlearn ``MetricFrame`` with ``true_positive_rate``
                  and ``equalized_odds_difference``.
Fallback: pure-Python TPR-per-group with no dependencies.

Usage
-----
    from src.tools.equal_opportunity import equal_opportunity

    result = equal_opportunity(
        y_true=[1, 0, 1, 1, 0],
        y_pred=[1, 0, 0, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        positive_label=1,
    )"""
from aaa.tools.equal_opportunity.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.equal_opportunity.compute.python import _compute_python, _empty_result  # noqa: F401
from aaa.tools.equal_opportunity.core import equal_opportunity  # noqa: F401
from aaa.tools.equal_opportunity.logger import logger  # noqa: F401

__all__ = [
    'logger',
    '_compute_fairlearn',
    '_compute_python',
    '_empty_result',
    'equal_opportunity',
]
