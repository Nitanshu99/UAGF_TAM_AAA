"""Logger and empty result for the subgroup_metrics tool.

The tool measures; it does not decide. Its accuracy-gap bands (0.10 PASS, 0.20
observations) had no source and were applied to the point estimate; the verdict
is now reached from the interval in :func:`aaa.tools.fairness_ci.annotate_metrics`.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)



def _empty_result(positive_label: Any) -> dict[str, Any]:
    """Return an empty subgroup-metrics result stub."""
    return {
        "metric": "subgroup_metrics",
        "groups": [],
        "accuracy_gap": None,
        "worst_group": None,
        "best_group": None,
        "verdict": "NOT_TESTED",
        # Not computed: no sample, rather than a sample of zero (T-20260913-033).
        "sample_size": None,
        "tool": None,
        "positive_label": str(positive_label),
    }
