"""Which cohorts a fairness decision compares, and at what adjusted confidence.

The pair a fairness metric reports is chosen *after* looking at the rates — the
most- against the least-selected cohort — so a 95 % interval for that pair alone
is too narrow: with enough cohorts, some pair lands outside by chance. Every pair
is therefore compared and the level is held across all of them (Bonferroni), so
the widest disparity cannot be manufactured by the number of cohorts.
"""
from __future__ import annotations

from itertools import combinations
from statistics import NormalDist

from aaa.tools.fairness_ci.logger import CONFIDENCE_LEVEL

#: ``{cohort: (successes, trials)}`` for one rate.
Counts = dict[str, tuple[int, int]]


def adjusted_z(comparisons: int) -> float:
    """Two-sided normal quantile holding :data:`CONFIDENCE_LEVEL` across *comparisons*.

    :param comparisons: Number of intervals the decision rests on (at least one).
    """
    return NormalDist().inv_cdf(1 - (1 - CONFIDENCE_LEVEL) / (2 * max(1, comparisons)))


def rate(counts: Counts, group: str) -> float:
    """*group*'s rate; only called for cohorts with at least one trial."""
    successes, trials = counts[group]
    return successes / trials


def ordered_pairs(counts: Counts, reference: str | None = None) -> list[tuple[str, str]]:
    """``(compared, baseline)`` pairs over the cohorts that hold a trial.

    Without a reference every pair is compared, lower rate first (ties on the
    name, so a re-run names the same pair). With a declared reference cohort — the
    client's own statement of which group is advantaged — each other cohort is
    compared with it, in that direction.

    :param counts: Successes and trials per cohort.
    :param reference: A declared baseline cohort, if any.
    """
    groups = sorted(g for g, (_, trials) in counts.items() if trials > 0)
    if reference is not None and str(reference) in groups:
        return [(g, str(reference)) for g in groups if g != str(reference)]
    return [tuple(sorted(pair, key=lambda g: (rate(counts, g), g)))  # type: ignore[misc]
            for pair in combinations(groups, 2)]


__all__ = ["Counts", "adjusted_z", "ordered_pairs", "rate"]
