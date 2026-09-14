"""The model's expected input matrix, from the bundle's encoders or the data dictionary."""
from __future__ import annotations

from typing import Any

from aaa.tools.eval_inputs.model_utils import _build_model_matrix


def build_model_matrix(result: Any, df: Any, feature_cols: Any, encoders: Any) -> Any:
    """Build and record the matrix the model is actually scored on.

    Every downstream tool that has to *run the model* (SHAP, LIME, the robustness
    probe) needs this matrix, not the raw frame. Discarding it after scoring is
    what left them all falling back to stubs on categorical data.

    :param result: The :class:`ScoredEvaluation` being filled, mutated in place.
    :param df: The evaluation frame.
    :param feature_cols: Feature columns the model bundle declared, if any.
    :param encoders: Encoders the model bundle shipped, if any.
    :returns: The matrix to score with.
    """
    X_model = (
        _build_model_matrix(df, feature_cols, encoders)
        if (feature_cols or encoders) else result.X_eval
    )
    result.X_model = X_model
    if isinstance(encoders, dict):
        result.categorical_features = [str(c) for c in encoders]
    return X_model


__all__ = ["build_model_matrix"]
