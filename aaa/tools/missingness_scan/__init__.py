"""missingness_scan — Per-column missingness rate scanner (§4.1).

Returns a structured dict compatible with T07_data_quality_report
``missingness`` block.

Uses only pandas — no heavy ML dependency.

Usage
-----
    from src.tools.missingness_scan import missingness_scan

    result = missingness_scan(df, high_missingness_threshold=20.0)"""
from aaa.tools.missingness_scan.core import missingness_scan  # noqa: F401
from aaa.tools.missingness_scan.logger import (  # noqa: F401
    _DEFAULT_THRESHOLD,
    _empty_result,
    logger,
)

__all__ = [
    'logger',
    '_DEFAULT_THRESHOLD',
    '_empty_result',
    'missingness_scan',
]
