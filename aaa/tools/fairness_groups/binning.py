"""Discretising a continuous protected attribute into comparable cohorts."""
from __future__ import annotations

from bisect import bisect_right
from typing import Any, Sequence

from aaa.tools.fairness_groups.logger import MAX_DISCRETE_LEVELS


def as_floats(values: Sequence[Any]) -> list[float] | None:
    """Return *values* as floats, or ``None`` if any of them is not numeric.

    ``bool`` is excluded deliberately: ``True``/``False`` is a two-level category
    that happens to be numeric, and binning it would be nonsense.
    """
    out: list[float] = []
    for value in values:
        if isinstance(value, bool) or value is None:
            return None
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            return None
    return out


def is_continuous(values: Sequence[Any], *, max_levels: int = MAX_DISCRETE_LEVELS) -> bool:
    """True when *values* are numeric with more distinct levels than a category has.

    :param values: The protected attribute's raw column.
    :param max_levels: Distinct values above which a numeric column is continuous.
    """
    numbers = as_floats(values)
    return numbers is not None and len(set(numbers)) > max_levels


def _fmt(value: float, integral: bool) -> str:
    return str(int(value)) if integral else f"{value:.4g}"


def bin_values(values: Sequence[Any], bins: int) -> list[str]:
    """Label each value with the quantile band it falls in.

    Bands are cut on quantiles rather than on an equal-width range so that each
    one is populated: an equal-width split of an age column puts almost nobody in
    the top band, which is the same n = 1 cohort problem one step along.  Labels
    name the band's observed range (``"18-27"``), so a reader sees the cohort
    rather than a bin index.

    :param values: The protected attribute's raw (numeric) column.
    :param bins: Number of bands to aim for; ties may yield fewer.
    :returns: One band label per input value, aligned with *values*.
    """
    numbers = as_floats(values) or []
    ordered = sorted(numbers)
    n = len(ordered)
    cuts = sorted({ordered[k * n // bins] for k in range(1, bins)} - {ordered[0]})
    index = [bisect_right(cuts, value) for value in numbers]

    integral = all(value.is_integer() for value in numbers)
    span: dict[int, tuple[float, float]] = {}
    for i, value in zip(index, numbers):
        low, high = span.get(i, (value, value))
        span[i] = (min(low, value), max(high, value))
    label = {i: (_fmt(low, integral) if low == high
                 else f"{_fmt(low, integral)}-{_fmt(high, integral)}")
             for i, (low, high) in span.items()}
    return [label[i] for i in index]


__all__ = ["as_floats", "is_continuous", "bin_values"]
