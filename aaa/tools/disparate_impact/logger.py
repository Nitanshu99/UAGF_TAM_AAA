"""Logger and result assembly for the disparate_impact tool.

The tool measures the ratio between two cohorts; it does not decide. The
four-fifths comparison it made on the point estimate, and the 0.60 band below it
that had no source, are gone: the verdict is reached from the interval over every
cohort pair in :func:`aaa.tools.fairness_ci.annotate_metrics`.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)



def _assemble_result(
    ratio: float | None,
    priv: str,
    unpriv: str,
    priv_rate: float,
    unpriv_rate: float,
    sample_size: int,
    tool: str,
    positive_label: Any,
    counts: tuple[tuple[int, int], tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """Common assembly for both aif360 and python paths.

    :param counts: ``((priv_selected, priv_n), (unpriv_selected, unpriv_n))``.
        Fix 30: the two denominators travel with the ratio, so a reader can see
        that ``0.660`` was a comparison against a ten-row cohort.
    """
    (priv_sel, priv_n), (unpriv_sel, unpriv_n) = counts or ((0, 0), (0, 0))
    return {
        "metric": "disparate_impact",
        "ratio": None if ratio is None else round(ratio, 6),
        "privileged_group": priv,
        "unprivileged_group": unpriv,
        "privileged_selection_rate": round(priv_rate, 6),
        "unprivileged_selection_rate": round(unpriv_rate, 6),
        "privileged_group_size": priv_n,
        "unprivileged_group_size": unpriv_n,
        "privileged_selected": priv_sel,
        "unprivileged_selected": unpriv_sel,
        # Decided from the interval by fairness_ci.annotate_metrics, not here.
        "four_fifths_rule_passed": None,
        "sample_size": sample_size,
        "tool": tool,
        "positive_label": str(positive_label),
    }
