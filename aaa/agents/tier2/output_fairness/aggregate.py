"""The worst-band rule that folds per-metric verdicts into one attribute verdict."""
from __future__ import annotations

from aaa.agents.tier2.output_fairness.context import FAIRNESS_VERDICT_ORDER


def aggregate_verdict(verdicts: list[str]) -> str:
    """Aggregate per-metric verdicts using the worst-band rule.

    :param verdicts: Individual metric verdicts.
    :returns: The worst non-``NOT_TESTED`` band, or ``NOT_TESTED``.
    """
    ranked = [v for v in verdicts if v in FAIRNESS_VERDICT_ORDER and v != "NOT_TESTED"]
    if not ranked:
        return "NOT_TESTED"
    return FAIRNESS_VERDICT_ORDER[max(FAIRNESS_VERDICT_ORDER.index(v) for v in ranked)]


__all__ = ["aggregate_verdict"]
