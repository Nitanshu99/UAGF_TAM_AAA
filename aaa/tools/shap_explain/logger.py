"""Part 1 of the former ``shap_explain`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


_DEFAULT_SAMPLE = 200


_DEFAULT_TOP_K = 20


def _row_count(X: Any) -> int:
    try:
        return int(len(X))
    except Exception:
        return 0


def _explain_shap(  # pragma: no cover
    model: Any,
    X: Any,
    names: list[str],
    sample_size: int,
    top_k: int,
) -> dict[str, Any]:
    """Run the real shap.Explainer pipeline."""
    import numpy as np  # type: ignore
    import shap  # type: ignore

    X_sample = X.head(sample_size) if hasattr(X, "head") else X[:sample_size]
    explainer = shap.Explainer(model, X_sample)
    # shap types __call__ as returning list[Explanation]; it returns a single
    # Explanation whose .values is an ndarray. Verified against binary,
    # multiclass and linear models — all yield technique='shap'.
    shap_values: Any = explainer(X_sample)

    # pylint reads shap's stub (list[Explanation]) and cannot see the `Any`
    # annotation above, so it flags .values as a list attribute. pyright is
    # satisfied by the annotation; only pylint needs the scoped exemption.
    vals = np.asarray(shap_values.values)  # pylint: disable=no-member
    if vals.ndim == 3:
        vals = np.abs(vals).mean(axis=2)
    importances = np.abs(vals).mean(axis=0).tolist()

    pairs = sorted(zip(names, importances), key=lambda p: abs(p[1]), reverse=True)[:top_k]
    feature_importance = [
        {"feature": str(n), "importance": float(v), "rank": i + 1}
        for i, (n, v) in enumerate(pairs)
    ]
    return {
        "technique": "shap",
        "feature_importance": feature_importance,
        "sample_size": _row_count(X_sample),
        "tool": "shap",
    }


def _columns_of(X: Any) -> list[str]:
    try:
        return [str(c) for c in X.columns]
    except Exception:
        return []
