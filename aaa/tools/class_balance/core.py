"""Part 2 of the former ``class_balance`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.class_balance.logger import (  # noqa: F401
    _DEFAULT_THRESHOLD,
    _assess_imbalance,
    _empty_result,
    logger,
)
from aaa.tools.fairness_groups import is_continuous


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

    if is_continuous(df[col].dropna().tolist()):
        # A continuous target has no classes: counting its distinct values as classes made
        # a forecaster's 'sales' column 92 classes, ratio 24.5, "severe" (T-20260913-091).
        logger.info("class_balance: target '%s' is continuous; class balance not measured.", col)
        return _empty_result(str(col), imbalance_threshold)

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

    imbalance_ratio, imbalance_detected, severity = _assess_imbalance(
        distribution, imbalance_threshold)

    return {
        "target_column": str(col),
        "class_distribution": distribution,
        "imbalance_detected": imbalance_detected,
        "imbalance_ratio": imbalance_ratio,
        "imbalance_severity": severity,
        "imbalance_threshold": imbalance_threshold,
    }
