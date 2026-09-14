"""Part 1 of the former ``robustness_probe`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)


#: Perturbation levels probed. For numeric columns a level is a fraction of that
#: column's own standard deviation; for categoricals the fraction of cells flipped;
#: for text the fraction of characters corrupted. Levels a provider declares are
#: probed as well (``degradation.declared_levels``).
_DEFAULT_EPSILONS = [0.05, 0.1, 0.2]

#: Seed of the probe's row sample and noise, so a rerun measures the same numbers.
PROBE_SEED = 123


def _perturb(X: Any, epsilon: float, modality: str,
             categorical_features: Sequence[str] = ()) -> Any:
    """Add Gaussian noise scaled to each numeric column's spread; typo noise on nlp text.

    The noise used to have standard deviation *epsilon* in the column's raw units —
    nothing on ``credit_amount`` (thousands), everything on a 0–1 feature — and was
    unseeded (T-20260914-006). Columns named in *categorical_features* are
    label-encoded identifiers, so they get a category flip instead
    (:mod:`aaa.tools.robustness_probe.categorical_perturb`).
    """
    if modality in {"llm", "agentic"}:
        return X  # prompt-level robustness is exercised by the UAGF-TAM-L suites
    if modality == "nlp":
        from aaa.tools.robustness_probe.text_perturb import perturb_text
        return perturb_text(X, epsilon)
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore

    rng = np.random.default_rng(PROBE_SEED + int(round(epsilon * 1000)))
    if isinstance(X, pd.DataFrame):
        from aaa.tools.robustness_probe.categorical_perturb import flip_categoricals
        categorical = {c for c in categorical_features if c in X.columns}
        X2 = flip_categoricals(X, epsilon, sorted(categorical)).copy()
        for col in X2.columns:
            if col not in categorical and pd.api.types.is_numeric_dtype(X2[col]):
                values = X2[col].astype(float)
                X2[col] = values + rng.normal(0.0, 1.0, len(X2)) * epsilon * float(values.std(ddof=0))
        return X2
    arr = np.asarray(X, dtype=float)
    return arr + rng.normal(0.0, 1.0, arr.shape) * epsilon * arr.std(axis=0, ddof=0)


def correct(y_true: Sequence[Any], y_pred: Sequence[Any]) -> list[bool]:
    """Per-row correctness, the unit the accuracy and its interval are computed from."""
    return [a == b for a, b in zip(y_true, y_pred)]


def _accuracy(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
    """Share of rows predicted correctly; callers only pass a non-empty sample."""
    flags = correct(y_true, y_pred)
    return sum(flags) / len(flags) if flags else 0.0
