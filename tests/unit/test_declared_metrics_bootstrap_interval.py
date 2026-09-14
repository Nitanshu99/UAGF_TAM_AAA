"""T-20260914-002: a declared metric is judged against the measured metric's interval.

A fixed 0.05 tolerance (and 0.10 for material, AUC >= 0.95 for leakage) judged
the same gap alike on 80 rows and on 80,000.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

from aaa.agents.tier2.model_validator.metrics import diff_declared_metrics
from aaa.tools.metric_suite.interval import bootstrap_intervals

_RNG = np.random.default_rng(7)
_TRUE = _RNG.integers(0, 2, 300).tolist()
_PRED = [t if _RNG.random() < 0.9 else 1 - t for t in _TRUE]
_PROBA = [min(1.0, max(0.0, p * 0.8 + _RNG.random() * 0.2)) for p in _PRED]


def test_intervals_contain_the_point_estimate_and_are_reproducible() -> None:
    """Accuracy, F1 and AUC intervals bracket their measured values; same seed, same answer."""
    names = ["accuracy", "f1", "roc_auc"]
    first = bootstrap_intervals(_TRUE, _PRED, _PROBA, 1, names)
    assert first == bootstrap_intervals(_TRUE, _PRED, _PROBA, 1, names)
    accuracy = float(np.mean(np.array(_TRUE) == np.array(_PRED)))
    assert first["accuracy"][0] <= accuracy <= first["accuracy"][1]
    assert first["roc_auc"][0] <= roc_auc_score(_TRUE, _PROBA) <= first["roc_auc"][1]
    assert bootstrap_intervals(_TRUE, _PRED, None, None, names).keys() == {"accuracy"}


def test_inside_corroborates_above_is_material_below_is_an_observation() -> None:
    """Case 01's figures: declared 0.935 inside [0.93, 0.98] is corroborated."""
    measured = {"metrics": {"accuracy": 0.957}}
    band = {"accuracy": (0.930, 0.980)}
    _, positives = diff_declared_metrics({"accuracy": 0.935}, measured, band)
    assert "corroborated" in positives[0]["description"]
    over, _ = diff_declared_metrics({"accuracy": 0.99}, measured, band)
    under, _ = diff_declared_metrics({"accuracy": 0.90}, measured, band)
    assert over[0]["materiality"] == "material" and "overstates" in over[0]["description"]
    assert under[0]["materiality"] == "possibly_material"


def test_without_an_interval_nothing_is_judged() -> None:
    """No interval, no corroboration and no finding."""
    assert diff_declared_metrics({"accuracy": 0.5}, {"metrics": {"accuracy": 0.9}}) == ([], [])
