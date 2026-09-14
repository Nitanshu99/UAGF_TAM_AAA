"""RAGAs metrics from however many golden-set samples the budget measured, with their uncertainty.

Case 04's 55 samples are 360 judge jobs; on the free route they cannot finish in the
L-branch budget, and on a paid route an evaluation cut at the deadline discards what it
already bought. Samples are taken in a seeded random order, a batch at a time, and every
completed batch is kept (T-20260914-017).
"""
from __future__ import annotations

from typing import Any

#: Seed of the sample order and of the bootstrap, so a rerun measures the same samples.
SEED = 123


def sample_order(population: int) -> list[int]:
    """A seeded permutation of the golden-set rows."""
    import numpy as np  # type: ignore

    return [int(i) for i in np.random.default_rng(SEED).permutation(population)]


def finite(values: Any) -> list[float]:
    """Per-sample scores ragas returned, without the NaNs of rows it could not score."""
    items = values if isinstance(values, (list, tuple)) else [values]
    return [float(v) for v in items if v is not None and float(v) == float(v)]


def aggregate(per_metric: dict[str, list[float]], measured: int, population: int,
              fields: tuple[str, ...]) -> dict[str, Any]:
    """Means, 95% bootstrap intervals and the sample they rest on, in T16's shape."""
    import numpy as np  # type: ignore

    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {field: None for field in fields}
    intervals: dict[str, list[float]] = {}
    for field, values in per_metric.items():
        if not values:
            continue
        arr = np.asarray(values)
        out[field] = float(arr.mean())
        means = arr[rng.integers(0, len(arr), size=(1000, len(arr)))].mean(axis=1)
        intervals[field] = [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]
    out.update(computed=True, sample_size=measured, population_size=population,
               intervals=intervals,
               reason=("" if measured == population else
                       f"measured on {measured} of {population} samples in seeded random order, "
                       "as many as the phase budget allowed"))
    return out


__all__ = ["SEED", "aggregate", "finite", "sample_order"]
