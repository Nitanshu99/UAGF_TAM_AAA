"""Part 1 of the former ``class_balance`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


_DEFAULT_THRESHOLD = 1.5  # majority:minority ratio above which imbalance is flagged


def _assess_imbalance(
    distribution: list[dict[str, Any]], threshold: float,
) -> tuple[float | None, bool | None, str | None]:
    """Rate the majority/minority ratio against *threshold*.

    :param distribution: Class distribution sorted by count descending.
    :param threshold: Ratio above which imbalance is flagged.
    :returns: ``(ratio, detected, severity)``; all ``None`` when fewer than two
        classes are present, since a ratio between classes is then undefined.
    """
    if len(distribution) < 2:
        return None, None, None
    majority_count = distribution[0]["count"]
    minority_count = distribution[-1]["count"]
    ratio = round(majority_count / minority_count, 4) if minority_count else None
    detected = ratio is not None and ratio > threshold
    if not detected or ratio is None:
        severity = "none"
    elif ratio < 3.0:
        severity = "mild"
    elif ratio < 10.0:
        severity = "moderate"
    else:
        severity = "severe"
    return ratio, detected, severity


def _empty_result(
    target_column: str | None,
    imbalance_threshold: float,
) -> dict[str, Any]:
    """Nothing counted: imbalance is unassessed (null), not "none" (T-20260913-062)."""
    return {
        "target_column": target_column,
        "class_distribution": [],
        "imbalance_detected": None,
        "imbalance_ratio": None,
        "imbalance_severity": None,
        "imbalance_threshold": imbalance_threshold,
    }
