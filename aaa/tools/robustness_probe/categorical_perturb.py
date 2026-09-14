"""Category-flip perturbation for label-encoded categorical features.

Gaussian noise is the right perturbation for a continuous feature and the wrong
one for a categorical: on a label-encoded column the integer is an identifier,
not a magnitude, so ``+N(0, 0.05)`` on ``checking_status`` neither corresponds
to any input the model can receive nor moves it far enough to test anything. A
tree ensemble splits between category indices, so small noise almost never
crosses a split and the probe reports a robustness it has not measured.

The categorical analogue of an epsilon-bounded perturbation is to resample the
category: flip a ``epsilon`` fraction of cells to a *different* observed value
of that column. Seeded, so T11 probe results are reproducible across re-runs.
"""
from __future__ import annotations

import random
from typing import Any, Sequence


def flip_categoricals(X: Any, epsilon: float, columns: Sequence[str],
                      seed: int = 42) -> Any:
    """Flip ``epsilon`` of each named column's cells to another observed value.

    :param X: pandas DataFrame holding the model's input matrix.
    :type X: Any
    :param epsilon: Fraction of rows to flip per column (0–1).
    :type epsilon: float
    :param columns: Categorical column names; anything absent from *X* is
        ignored, so the caller may pass the full declared list.
    :type columns: Sequence[str]
    :param seed: RNG seed for reproducible probes.
    :type seed: int
    :returns: A copy of *X* with the named columns perturbed; *X* unchanged
        when it is not a DataFrame, ``epsilon <= 0``, or no column matches.
    :rtype: Any
    """
    named = [c for c in columns if c in getattr(X, "columns", [])]
    if epsilon <= 0 or not named:
        return X
    rng = random.Random(seed)
    X2 = X.copy()
    for col in named:
        values = list(dict.fromkeys(X2[col].tolist()))
        if len(values) < 2:
            continue
        X2[col] = [
            _flip(v, values, rng) if rng.random() < epsilon else v
            for v in X2[col]
        ]
    return X2


def _flip(value: Any, values: list[Any], rng: random.Random) -> Any:
    """Draw a value from *values* other than *value*."""
    alternatives = [v for v in values if v != value]
    return rng.choice(alternatives) if alternatives else value


__all__ = ["flip_categoricals"]
