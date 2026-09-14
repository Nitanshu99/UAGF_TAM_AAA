"""class_balance — Class distribution and imbalance detector (§4.1).

Returns a structured dict compatible with T07_data_quality_report
``class_balance`` block.

Production path:  scikit-learn ``compute_class_weight`` for imbalance ratio.
Fallback: pure-pandas value_counts if sklearn unavailable.

Usage
-----
    from src.tools.class_balance import class_balance

    result = class_balance(df, target_column="class", imbalance_threshold=1.5)"""
from aaa.tools.class_balance.core import class_balance  # noqa: F401
from aaa.tools.class_balance.logger import (  # noqa: F401
    _DEFAULT_THRESHOLD,
    _assess_imbalance,
    _empty_result,
    logger,
)

__all__ = [
    'logger', '_DEFAULT_THRESHOLD', '_assess_imbalance', '_empty_result', 'class_balance',
]
