"""Saying how a protected attribute was grouped, or why it could not be compared."""
from __future__ import annotations

from collections import Counter
from typing import Any, Sequence


def _reason(attribute: str, values: Sequence[Any], counts: Counter, smallest: int,
            binned: bool, tested: bool) -> str:
    """Say in one sentence how the attribute was grouped, or why it was not compared."""
    origin = (f"continuous attribute with {len(set(str(v) for v in values))} distinct "
              f"values binned into {len(counts)} band(s)" if binned
              else f"{len(counts)} categorical group(s)")
    if tested:
        return f"{attribute}: {origin}; smallest group n={smallest}."
    return (f"{attribute}: only {len(counts)} group present — a group-fairness "
            f"metric needs at least two cohorts to compare.")


__all__ = ["_reason"]
