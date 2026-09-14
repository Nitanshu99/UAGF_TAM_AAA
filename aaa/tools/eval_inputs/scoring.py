"""Task-type inference and defensive model scoring."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _infer_task_type(model: Any, y_true: list[Any] | None) -> str:
    """Classify the learning task so fairness semantics apply correctly.

    Group-fairness metrics (disparate impact, equal opportunity) only make
    sense for a *classification* output. A forecaster (regressor) or an
    anomaly detector is a different problem where per-group parity is not
    the relevant test.
    """
    name = type(model).__name__.lower()
    if any(k in name for k in ("isolationforest", "oneclass", "localoutlier", "ellipticenvelope")):
        return "anomaly"
    if "regress" in name:
        return "regression"
    if y_true:
        distinct = {v for v in y_true if v is not None}
        if 0 < len(distinct) <= 20:
            return "classification"
        return "regression"
    if "classif" in name:
        return "classification"
    return "unknown"


def _predict(model: Any, X: Any, predictor: Any = None) -> tuple[list[Any] | None, list[float] | None]:
    """Score X defensively through *predictor* (label space) or ``model.predict``; failure → ``(None, None)``."""
    try:
        y_pred = list(predictor(X)) if predictor is not None else list(model.predict(X))
    except Exception as exc:  # noqa: BLE001
        logger.info("model.predict failed (%s); evaluation unscored.", exc)
        return None, None
    y_proba: list[float] | None = None
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)
            if hasattr(proba, "shape") and len(proba.shape) == 2 and proba.shape[1] == 2:
                y_proba = [float(row[1]) for row in proba]
        except Exception as exc:  # noqa: BLE001
            logger.info("model.predict_proba failed (%s); AUC unavailable.", exc)
    return y_pred, y_proba
