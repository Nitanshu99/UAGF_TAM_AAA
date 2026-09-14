"""Part 1 of the former ``missingness_scan`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


_DEFAULT_THRESHOLD = 20.0  # percent — columns above this are "high missingness"


def _empty_result(threshold: float) -> dict[str, Any]:
    """Nothing scanned: no columns, and a missingness share that is null, not 0 %.

    An empty or absent frame has no cells, so "0.0 % missing" would report a
    measurement that was never taken (T-20260913-062).
    """
    return {
        "columns": [],
        "overall_missingness_pct": None,
        "high_missingness_columns": [],
        "threshold_used": threshold,
    }
