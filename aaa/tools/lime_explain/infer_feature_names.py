"""Part 5 of the former ``lime_explain`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.lime_explain.explain.lime import _explain_lime  # noqa: F401
from aaa.tools.lime_explain.logger import (  # noqa: F401
    _DEFAULT_NUM_FEATURES,
    _DEFAULT_NUM_INSTANCES,
    logger,
)
from aaa.tools.lime_explain.row_count import _is_numeric, _row_count  # noqa: F401


def _infer_feature_names(X: Any) -> list[str]:
    try:
        return [str(c) for c in X.columns]
    except Exception:
        try:
            return [f"f{i}" for i in range(X.shape[1])]
        except Exception:
            return []


def lime_explain(
    model: Any = None,
    X: Any = None,
    feature_names: Sequence[str] | None = None,
    class_names: Sequence[str] | None = None,
    num_instances: int = _DEFAULT_NUM_INSTANCES,
    num_features: int = _DEFAULT_NUM_FEATURES,
    reasons: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Generate per-instance local explanations.

    Parameters
    ----------
    model:
        Trained classifier exposing ``predict_proba``.  Optional —
        when None we return a feature-snapshot stub.
    X:
        Tabular feature matrix.
    feature_names:
        Column names; inferred from ``X.columns`` if available.
    class_names:
        Class labels for the classifier output.
    num_instances:
        Number of representative instances to explain.
    num_features:
        Maximum number of top features per instance.

    Returns
    -------
    list of dicts matching the T10 ``local_explanations`` item schema.
    """
    if X is None or _row_count(X) == 0:
        return []

    names = list(feature_names) if feature_names else _infer_feature_names(X)
    if not names:
        return []

    if model is None:
        return []
    try:
        return _explain_lime(model, X, names, class_names, num_instances, num_features)
    except Exception as exc:
        logger.info("LIME unavailable (%s); no local explanations reported.", exc)
        if reasons is not None:
            reasons.append(f"LIME could not run on the supplied matrix: {exc}")
        return []
