"""Interval estimators for a proportion, a difference of proportions, and a ratio.

Wilson rather than Wald throughout, and Newcombe's hybrid for the difference:
the Wald interval collapses to zero width at a selection rate of 0 or 1, which
is exactly where this system's small cohorts land — six of `age`'s 45 cohorts sat
at 0.0 and two at 1.0.  An interval that reports ±0.000 on a one-row group is
worse than no interval at all.
"""
from __future__ import annotations

from math import exp, log, sqrt

from aaa.tools.fairness_ci.logger import Z


def wilson(successes: int, n: int, z: float = Z) -> tuple[float | None, float | None]:
    """Wilson score interval for a single proportion.

    :param successes: Favourable outcomes in the group.
    :param n: Group size.
    :param z: Normal quantile; a multiplicity-adjusted one when several are compared.
    :returns: ``(low, high)``; ``(None, None)`` for an empty group, which has no
        proportion to bound — ``(0.0, 1.0)`` was once reported in its place.
    """
    if n <= 0:
        return None, None
    return _wilson(successes, n, z)


def _wilson(successes: int, n: int, z: float = Z) -> tuple[float, float]:
    """Wilson bounds for a non-empty group (``n > 0``)."""
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def difference_ci(a: tuple[int, int], b: tuple[int, int],
                  z: float = Z) -> tuple[float | None, float | None]:
    """Newcombe hybrid-score interval for ``p(a) − p(b)``.

    :param a: ``(successes, n)`` for the higher-rate group.
    :param b: ``(successes, n)`` for the lower-rate group.
    :param z: Normal quantile for the two Wilson intervals it combines.
    :returns: ``(low, high)`` for the difference, or ``(None, None)`` when either
        group is empty (the hard-coded ``(-1.0, 1.0)`` it replaced was no estimate).
    """
    (a_s, a_n), (b_s, b_n) = a, b
    if a_n <= 0 or b_n <= 0:
        return None, None
    p_a, p_b = a_s / a_n, b_s / b_n
    a_low, a_high = _wilson(a_s, a_n, z)
    b_low, b_high = _wilson(b_s, b_n, z)
    delta = p_a - p_b
    low = delta - sqrt((p_a - a_low) ** 2 + (b_high - p_b) ** 2)
    high = delta + sqrt((a_high - p_a) ** 2 + (p_b - b_low) ** 2)
    return max(-1.0, low), min(1.0, high)


def ratio_ci(numerator: tuple[int, int], denominator: tuple[int, int],
             z: float = Z) -> tuple[float | None, float | None]:
    """Katz log interval for the ratio ``p(numerator) / p(denominator)``.

    An empty cell of either 2×2 row — no selections, or every row selected —
    makes the log ratio's variance undefined or zero, so Haldane's correction adds
    0.5 to each cell (one row to the group). An all-selected pair of three-row
    groups once reported the interval ``[1, 1]``: certainty from six rows.

    :param numerator: ``(successes, n)`` for the unprivileged group.
    :param denominator: ``(successes, n)`` for the privileged group.
    :param z: Normal quantile; a multiplicity-adjusted one when several are compared.
    :returns: ``(low, high)``, or ``(None, None)`` when either group is empty.
    """
    (x1, n1), (x2, n2) = numerator, denominator
    if n1 <= 0 or n2 <= 0:
        return None, None
    a1, m1, a2, m2 = float(x1), float(n1), float(x2), float(n2)
    if 0 in (x1, x2) or x1 == n1 or x2 == n2:
        a1, m1, a2, m2 = a1 + 0.5, m1 + 1.0, a2 + 0.5, m2 + 1.0
    p1, p2 = a1 / m1, a2 / m2
    se = sqrt((1 - p1) / a1 + (1 - p2) / a2)
    centre = log(p1 / p2)
    return exp(centre - z * se), exp(centre + z * se)


__all__ = ["wilson", "difference_ci", "ratio_ci"]
