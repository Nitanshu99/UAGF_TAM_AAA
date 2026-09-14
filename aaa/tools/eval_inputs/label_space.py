"""Putting a model's predictions into the evaluation set's own label space.

scikit-learn's outlier detectors (IsolationForest, OneClassSVM, LocalOutlierFactor,
EllipticEnvelope) predict ``-1`` for an outlier and ``+1`` for an inlier. Case 03's
evaluation set labels an anomaly ``1`` and normal operation ``0``, and the raw
predictions were compared with those labels directly: accuracy 0.014, a clean
robustness pass of 0.02, and a material "robustness FAILED" finding that measured
the encoding, not the model (2026-09-13). Every consumer — the metric suite, the
Phase 3 probe and the Tier-3 cyber probe — now scores through one predictor.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

OUTLIER, INLIER = -1, 1


def _binary(values: Sequence[Any] | None) -> set[Any]:
    distinct = {v for v in (values or []) if v is not None}
    return distinct if distinct and distinct <= {0, 1} else set()


def label_space_predictor(model: Any, task_type: str, y_true: Sequence[Any] | None,
                          positive_label: Any = 1) -> Callable[[Any], list[Any]] | None:
    """A ``predict`` whose outputs use the evaluation labels, or ``None`` without a model.

    :param model: The loaded estimator.
    :param task_type: ``_infer_task_type``'s answer.
    :param y_true: The evaluation labels.
    :param positive_label: The label that means "anomaly" (the data dictionary's positive label).
    """
    if model is None or not hasattr(model, "predict"):
        return None
    labels = _binary(y_true)
    if task_type != "anomaly" or not labels:
        return lambda X: list(model.predict(X))
    normal = 0 if positive_label == 1 else 1

    def predict(X: Any) -> list[Any]:
        raw = list(model.predict(X))
        if not {int(p) for p in raw} <= {OUTLIER, INLIER}:
            return raw  # already in label space (a wrapper that maps it itself)
        return [positive_label if int(p) == OUTLIER else normal for p in raw]
    return predict


__all__ = ["INLIER", "OUTLIER", "label_space_predictor"]
