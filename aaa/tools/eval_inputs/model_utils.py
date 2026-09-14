"""Model-bundle unwrapping, matrix building, and task-type inference."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _unwrap_model_bundle(obj: Any) -> tuple[Any, Any, Any]:
    """Return ``(estimator, encoders, feature_cols)`` from a model or a bundle dict.

    Real-world artefacts are routinely saved as a bundle
    ``{'model': <estimator>, 'encoders': {col: LabelEncoder}, 'feature_cols': [...]}``
    rather than a bare estimator. Unwrap so the fitted model can actually be
    scored; a bare estimator passes through unchanged.
    """
    if callable(getattr(obj, "predict", None)):
        return obj, None, None
    if isinstance(obj, dict):
        estimator = (
            obj.get("model") or obj.get("estimator") or obj.get("clf") or obj.get("pipeline")
        )
        if not callable(getattr(estimator, "predict", None)):
            estimator = next(
                (v for v in obj.values() if callable(getattr(v, "predict", None))), None
            )
        return estimator, obj.get("encoders"), obj.get("feature_cols")
    return None, None, None


def _build_model_matrix(df: Any, feature_cols: Any, encoders: Any) -> Any:
    """Select the model's ``feature_cols`` (order preserved) and apply its encoders.

    Categorical columns named in *encoders* are label-encoded with the fitted
    classes; values unseen at training map to ``-1`` so scoring degrades
    gracefully instead of raising. Returns a DataFrame ready for ``predict``.
    """
    cols = [c for c in (feature_cols or list(df.columns)) if c in df.columns]
    X = df[cols].copy()
    if isinstance(encoders, dict):
        for col, enc in encoders.items():
            if col not in X.columns:
                continue
            classes_attr = getattr(enc, "classes_", None)
            classes = list(classes_attr) if classes_attr is not None else []
            if not classes:
                continue
            mapping = {cls: idx for idx, cls in enumerate(classes)}
            X[col] = X[col].map(lambda v, m=mapping: m.get(v, -1))
    return X
