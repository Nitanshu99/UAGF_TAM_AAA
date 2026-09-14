"""demographic_parity — Demographic-parity fairness metric (§4.3).

Returns a structured dict compatible with the T12_output_fairness_report
``demographic_parity`` block.

Production path:  fairlearn ``MetricFrame`` / ``demographic_parity_difference``
                  and ``demographic_parity_ratio``.
Fallback: pure-Python selection-rate per group with no dependencies.

Usage
-----
    from src.tools.demographic_parity import demographic_parity

    result = demographic_parity(
        y_pred=[1, 0, 1, 1, 0],
        sensitive_features=["M", "F", "M", "F", "F"],
        positive_label=1,
    )"""
from aaa.tools.demographic_parity.compute.fairlearn import _compute_fairlearn  # noqa: F401
from aaa.tools.demographic_parity.compute.python import _compute_python  # noqa: F401
from aaa.tools.demographic_parity.empty_result import (  # noqa: F401
    _empty_result,
    demographic_parity,
)
from aaa.tools.demographic_parity.logger import logger  # noqa: F401

__all__ = [
    'logger',
    '_compute_fairlearn',
    '_compute_python',
    '_empty_result',
    'demographic_parity',
]
