"""Character-level text perturbation for the NLP robustness probe.

Provides the real perturbation behind ``_perturb``'s ``nlp`` branch: seeded
typo-style corruption (adjacent swap / drop / substitute) applied to every
string cell, with ``epsilon`` as the approximate fraction of characters
corrupted per cell. Deterministic for a given seed so T11 probe results are
reproducible across audit re-runs.
"""
from __future__ import annotations

import random
from typing import Any

_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def corrupt_text(text: str, epsilon: float, rng: random.Random) -> str:
    """Apply ``round(epsilon * len(text))`` (min 1) typo edits to *text*.

    :param text: The clean input string.
    :type text: str
    :param epsilon: Fraction of characters to corrupt (0–1).
    :type epsilon: float
    :param rng: Seeded generator so probes are reproducible.
    :type rng: random.Random
    :returns: The corrupted string; empty input or ``epsilon <= 0`` returns
        the input unchanged.
    :rtype: str
    """
    chars = list(text)
    if not chars or epsilon <= 0:
        return text
    for _ in range(max(1, round(epsilon * len(chars)))):
        i = rng.randrange(len(chars))
        op = rng.choice(("swap", "drop", "sub"))
        if op == "swap" and i + 1 < len(chars):
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
        elif op == "drop" and len(chars) > 1:
            del chars[i]
        else:
            chars[i] = rng.choice(_ALPHABET)
    return "".join(chars)


def perturb_text(X: Any, epsilon: float, seed: int = 42) -> Any:
    """Corrupt the string content of *X*, leaving numeric columns untouched.

    :param X: pandas DataFrame / Series, or any sequence of strings.
    :type X: Any
    :param epsilon: Fraction of characters to corrupt per cell.
    :type epsilon: float
    :param seed: RNG seed for reproducible probes.
    :type seed: int
    :returns: A corrupted copy with the same shape/container as *X*.
    :rtype: Any
    """
    rng = random.Random(seed)
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return [corrupt_text(str(v), epsilon, rng) for v in X]
    if isinstance(X, pd.DataFrame):
        X2 = X.copy()
        for col in X2.columns:
            if pd.api.types.is_string_dtype(X2[col]) or pd.api.types.is_object_dtype(X2[col]):
                X2[col] = [corrupt_text(str(v), epsilon, rng) for v in X2[col]]
        return X2
    if isinstance(X, pd.Series):
        return pd.Series([corrupt_text(str(v), epsilon, rng) for v in X], index=X.index)
    return [corrupt_text(str(v), epsilon, rng) for v in X]
