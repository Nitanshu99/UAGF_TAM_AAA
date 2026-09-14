"""Input and output shape of a loaded model, from the attributes it carries."""
from __future__ import annotations

from typing import Any

from aaa.tools.model_meta.introspect.params import final_estimator, hyperparameters, parameter_count


def _output_shape(estimator: Any) -> str | None:
    """What ``predict`` returns, by the estimator's kind (scikit-learn's own tags)."""
    if not hasattr(estimator, "predict"):
        return None
    try:
        from sklearn.base import is_classifier, is_outlier_detector, is_regressor
    except ImportError:
        return None
    if is_outlier_detector(estimator):
        return "(n_samples,) inlier/outlier label (+1 / -1)"
    classes = getattr(estimator, "classes_", None)
    if is_classifier(estimator) and classes is not None:
        return f"(n_samples,) class label, {len(classes)} classes"
    if is_regressor(estimator):
        return "(n_samples,) predicted value"
    return None


def model_facts(model: Any) -> dict[str, Any]:
    """The architecture and configuration facts *model* states about itself.

    :param model: The model Phase 3 loaded, or ``None``.
    :returns: ``input_shape``, ``output_shape``, ``parameter_count`` and
        ``hyperparameters``; each ``None`` when the model does not carry it.
    """
    if model is None:
        return {"input_shape": None, "output_shape": None, "parameter_count": None,
                "hyperparameters": None}
    features = getattr(model, "n_features_in_", None)
    return {
        "input_shape": f"(n_samples, {int(features)})" if features is not None else None,
        "output_shape": _output_shape(final_estimator(model)),
        "parameter_count": parameter_count(model),
        "hyperparameters": hyperparameters(model),
    }
