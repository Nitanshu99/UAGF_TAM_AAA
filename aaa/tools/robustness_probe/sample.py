"""Sampling the evaluation set and taking the clean pass the probes are measured against."""
from __future__ import annotations

from typing import Any, Callable, Sequence

from aaa.tools.fairness_groups import is_continuous
from aaa.tools.robustness_probe.logger import PROBE_SEED, _accuracy, correct, logger
from aaa.tools.robustness_probe.verdict import _empty_result


def prepare_sample(X: Any, y_true: Sequence[Any] | None, model: Any,
                   predict_fn: Callable[[Any], Sequence[Any]] | None,
                   sample_size: int | None, modality: str) -> dict[str, Any]:
    """Take the sample and its clean accuracy, or an empty result saying why not.

    :param X: Feature matrix or text inputs.
    :param y_true: Ground-truth labels.
    :param model: Trained model, used for ``predict`` when no *predict_fn* is given.
    :param predict_fn: Callable ``X -> y_pred``.
    :param sample_size: Maximum rows to probe; ``None`` probes every row.
    :param modality: The system's modality, for the empty result.
    :returns: ``{"sample": (n, y, X_sample, predictor, clean_accuracy)}``, or the
        empty result (which carries ``probes``) when the probe cannot run.
    """
    if X is None or y_true is None or len(y_true) == 0:
        return _empty_result(modality)
    n = len(y_true) if sample_size is None else min(sample_size, len(y_true))
    rows = _rows(len(y_true), n)
    y = [list(y_true)[i] for i in rows]
    if is_continuous(y):
        # Exact-match accuracy of a forecast is 0.0 by construction, so every probe
        # "measured" 0.0 and the verdict came out FAIL (case 02, 2026-09-13).
        return _empty_result(modality, reason=(
            "the target is continuous (forecasting or regression): accuracy-based "
            "perturbation probes are undefined for it, so robustness was not measured"))
    X_sample = X.iloc[rows] if hasattr(X, "iloc") else [X[i] for i in rows]
    predictor = predict_fn or (model.predict
                               if model is not None and hasattr(model, "predict") else None)
    if predictor is None:
        return _empty_result(modality, reason="No model.predict or predict_fn supplied.")
    try:
        clean_pred = list(predictor(X_sample))
    except Exception as exc:  # noqa: BLE001 - a stub is the honest answer here
        logger.info("Clean prediction failed (%s); returning stub.", exc)
        return _empty_result(modality, reason=f"clean prediction failed: {exc}")
    clean_accuracy = _accuracy(y, clean_pred)
    if clean_accuracy == 0.0:
        return _empty_result(modality, reason=(
            "the model is wrong on every clean sample, so attack success is undefined"))
    return {"sample": (n, y, X_sample, predictor, clean_accuracy), "clean": correct(y, clean_pred)}


def _rows(total: int, n: int) -> list[int]:
    """A seeded draw of *n* row positions, in file order; every row when *n* covers them.

    ``head(n)`` of a sorted file is not a sample of it (T-20260914-006).
    """
    if n >= total:
        return list(range(total))
    import numpy as np  # type: ignore

    return sorted(int(i) for i in np.random.default_rng(PROBE_SEED).choice(total, n, replace=False))


__all__ = ["prepare_sample"]
