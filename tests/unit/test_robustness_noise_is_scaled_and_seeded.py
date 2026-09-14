"""T-20260914-006: robustness noise is a fraction of each feature's spread, and reproducible.

Noise of standard deviation 0.1 in raw units did nothing to ``credit_amount`` and
everything to a 0–1 feature; the noise was unseeded and the rows were ``head(n)``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from aaa.tools.robustness_probe.logger import _perturb
from aaa.tools.robustness_probe.sample import _rows


def test_noise_is_the_same_fraction_of_every_columns_spread() -> None:
    """Amounts in thousands and a 0–1 score move by the same share of their spread."""
    rng = np.random.default_rng(0)
    frame = pd.DataFrame({"credit_amount": rng.normal(3000, 2500, 2000),
                          "score": rng.uniform(0, 1, 2000)})
    moved = _perturb(frame, 0.2, "tabular") - frame
    for col in frame.columns:
        assert abs(moved[col].std() / frame[col].std() - 0.2) < 0.02


def test_the_probe_is_reproducible_and_samples_the_whole_file() -> None:
    """Same seed, same noise and rows; the rows are not the first n."""
    frame = pd.DataFrame({"x": np.arange(1000, dtype=float)})
    assert _perturb(frame, 0.1, "tabular").equals(_perturb(frame, 0.1, "tabular"))
    rows = _rows(1000, 200)
    assert rows == _rows(1000, 200) and rows != list(range(200)) and max(rows) > 800
    assert _rows(50, 200) == list(range(50))
