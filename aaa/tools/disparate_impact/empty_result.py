"""Part 3 of the former ``disparate_impact`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.disparate_impact.compute.aif360 import _compute_aif360  # noqa: F401
from aaa.tools.disparate_impact.logger import _assemble_result, logger  # noqa: F401


def _empty_result(privileged_group: Any | None, positive_label: Any) -> dict[str, Any]:
    """Return an empty disparate-impact result stub."""
    return {
        "metric": "disparate_impact",
        "ratio": None,
        "privileged_group": str(privileged_group) if privileged_group is not None else None,
        "unprivileged_group": None,
        "privileged_selection_rate": None,
        "unprivileged_selection_rate": None,
        "four_fifths_rule_passed": None,
        "verdict": "NOT_TESTED",
        # Not computed: no sample, rather than a sample of zero (T-20260913-033).
        "sample_size": None,
        "tool": None,
        "positive_label": str(positive_label),
    }
