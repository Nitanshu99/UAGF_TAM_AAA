"""Which output of a model LIME explains, and in which mode.

LIME was only ever handed ``predict_proba``, so an outlier detector or a regressor
— neither has one — got no local explanations at all (case 03, 2026-09-13; the
Verifier raised Art. 13(3) against the empty list). LIME's regression mode explains
any real-valued output: a detector's anomaly score or a regressor's prediction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class LimeTarget:
    """The model output to explain."""

    mode: str
    predict: Callable[[Any], Any]
    output: str


def lime_target(model: Any) -> LimeTarget:
    """Pick the output LIME explains for *model*.

    :raises ValueError: When the model exposes no output LIME can explain.
    """
    if callable(getattr(model, "predict_proba", None)):
        return LimeTarget("classification", model.predict_proba, "class probability")
    if callable(getattr(model, "decision_function", None)) and _is_outlier_detector(model):
        return LimeTarget("regression", model.decision_function,
                          "anomaly score (decision_function; negative = outlier)")
    if callable(getattr(model, "predict", None)):
        return LimeTarget("regression", model.predict, "predicted value")
    raise ValueError("the model exposes neither predict_proba, decision_function nor predict")


def _is_outlier_detector(model: Any) -> bool:
    """scikit-learn's own tag, on the model or a pipeline's final step."""
    try:
        from sklearn.base import is_outlier_detector
    except ImportError:
        return False
    steps = getattr(model, "steps", None)
    return bool(is_outlier_detector(steps[-1][1] if isinstance(steps, list) and steps else model))
