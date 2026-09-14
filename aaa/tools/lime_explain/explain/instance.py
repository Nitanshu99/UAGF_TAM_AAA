"""One LIME instance explanation, read off the label the explainer actually explained."""
from __future__ import annotations

from typing import Any

from aaa.tools.lime_explain.explain.target import LimeTarget


def explain_one(explainer: Any, target: LimeTarget, X_arr: Any, i: int, num_features: int,
                classes: list | None) -> dict[str, Any]:
    """Explain instance *i* and return its record.

    ``top_labels`` is only populated when the caller asked for it; we do not, so it
    is ``None`` and label 0 is not necessarily one LIME explained. For a binary
    classifier it explains label 1 alone, and ``as_list(label=0)`` raises KeyError —
    which a per-instance handler then swallowed, emptying the whole result. In
    regression mode the label is ignored and the explained value is the output's own.

    :param explainer: The ``LimeTabularExplainer``.
    :param target: The model output being explained.
    :param X_arr: The feature matrix as an array.
    :param i: Row index to explain.
    :param num_features: How many features to report.
    :param classes: Class names, when the caller supplied them.
    :returns: The instance record; ``explained_output`` is diagnostic and stripped from T10.
    """
    exp = explainer.explain_instance(data_row=X_arr[i], predict_fn=target.predict,
                                     num_features=num_features)
    if target.mode == "regression":
        return _record(i, float(exp.predicted_value), None, exp.as_list(), target.output)
    labels = list(exp.top_labels or exp.available_labels() or [0])
    top_label = labels[0]
    probs = exp.predict_proba.tolist() if exp.predict_proba is not None else []
    label_name = (str(classes[top_label])
                  if classes and 0 <= top_label < len(classes)
                  else str(top_label))
    return _record(i, label_name, float(max(probs)) if probs else None,
                   exp.as_list(label=top_label), target.output)


def _record(i: int, prediction: Any, probability: float | None,
            weights: list[tuple[Any, float]], output: str) -> dict[str, Any]:
    """One T10 local-explanation item."""
    return {
        "instance_id": f"instance_{i}",
        "prediction": prediction,
        "predicted_probability": probability,
        "top_features": [{"feature": str(f), "contribution": float(c)} for f, c in weights],
        "explained_output": output,
    }


__all__ = ["explain_one"]
