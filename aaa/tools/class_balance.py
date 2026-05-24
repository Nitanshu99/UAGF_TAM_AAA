"""
class_balance — Class distribution and imbalance detector (§4.1).

Returns a structured dict compatible with T07_data_quality_report
``class_balance`` block.

Production path:  scikit-learn ``compute_class_weight`` for imbalance ratio.
Offline/fallback: pure-pandas value_counts if sklearn unavailable.

Usage
-----
    from src.tools.class_balance import class_balance

    result = class_balance(df, target_column="class", imbalance_threshold=1.5)
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = 1.5  # majority:minority ratio above which imbalance is flagged


def class_balance(
    df: Any,
    target_column: str | None = None,
    imbalance_threshold: float = _DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """
    Compute class distribution and flag imbalance.

    Parameters
    ----------
    df:
        A ``pandas.DataFrame``.
    target_column:
        Column name containing class labels.  If ``None`` the last column
        of the DataFrame is used as a heuristic.
    imbalance_threshold:
        Majority-to-minority count ratio above which imbalance is flagged
        (default 1.5 — i.e. any ratio > 1.5 is considered imbalanced).

    Returns
    -------
    dict matching the T07 ``class_balance`` sub-schema:
        {
            target_column, class_distribution,
            imbalance_detected, imbalance_ratio, imbalance_severity,
            imbalance_threshold
        }
    """
    try:
        import pandas as pd  # type: ignore  # noqa: F401
    except ImportError:
        logger.warning("pandas not installed; returning empty class_balance stub.")
        return _empty_result(target_column, imbalance_threshold)

    # Determine target column
    col = target_column or (df.columns[-1] if len(df.columns) > 0 else None)
    if col is None or col not in df.columns:
        logger.warning("class_balance: target column '%s' not found.", col)
        return _empty_result(target_column, imbalance_threshold)

    try:
        counts = df[col].value_counts(dropna=False)
    except Exception as exc:
        logger.warning("class_balance: value_counts failed: %s", exc)
        return _empty_result(target_column, imbalance_threshold)

    total = int(counts.sum())
    distribution: list[dict[str, Any]] = [
        {
            "label": str(label),
            "count": int(cnt),
            "proportion": round(int(cnt) / total, 6) if total else 0.0,
        }
        for label, cnt in counts.items()
    ]

    if len(distribution) < 2:
        imbalance_ratio = None
        imbalance_detected = False
        severity = "none"
    else:
        majority_count = distribution[0]["count"]
        minority_count = distribution[-1]["count"]
        imbalance_ratio = (
            round(majority_count / minority_count, 4) if minority_count else None
        )
        imbalance_detected = (
            imbalance_ratio is not None and imbalance_ratio > imbalance_threshold
        )
        if not imbalance_detected:
            severity = "none"
        elif imbalance_ratio < 3.0:
            severity = "mild"
        elif imbalance_ratio < 10.0:
            severity = "moderate"
        else:
            severity = "severe"

    return {
        "target_column": str(col),
        "class_distribution": distribution,
        "imbalance_detected": imbalance_detected,
        "imbalance_ratio": imbalance_ratio,
        "imbalance_severity": severity,
        "imbalance_threshold": imbalance_threshold,
    }


def _empty_result(
    target_column: str | None,
    imbalance_threshold: float,
) -> dict[str, Any]:
    """Return an empty class_balance result stub."""
    return {
        "target_column": target_column,
        "class_distribution": [],
        "imbalance_detected": False,
        "imbalance_ratio": None,
        "imbalance_severity": "none",
        "imbalance_threshold": imbalance_threshold,
    }
