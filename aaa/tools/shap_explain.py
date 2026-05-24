"""
shap_explain — SHAP-based global feature importance (§4.2).

Returns a structured dict compatible with the T10_explainability_report
``global_explanation`` block.

Production path:  ``shap.Explainer`` (TreeExplainer / KernelExplainer /
                  PermutationExplainer auto-detected by SHAP) for tabular
                  or NLP feature inputs.
Offline/fallback: pandas-based variance-weighted feature importance —
                  no external dependency.

Usage
-----
    from src.tools.shap_explain import shap_explain

    result = shap_explain(model=clf, X=X_test, feature_names=cols)
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

_DEFAULT_SAMPLE = 200
_DEFAULT_TOP_K = 20


def shap_explain(
    model: Any = None,
    X: Any = None,
    feature_names: Sequence[str] | None = None,
    sample_size: int = _DEFAULT_SAMPLE,
    top_k: int = _DEFAULT_TOP_K,
) -> dict[str, Any]:
    """
    Compute global feature importance via SHAP (or fallback heuristic).

    Parameters
    ----------
    model:
        Trained model with ``predict`` / ``predict_proba``.  Optional —
        if None we fall back to variance-based importance over ``X``.
    X:
        Tabular feature matrix (``pandas.DataFrame`` or 2-D array).
    feature_names:
        Column names; inferred from ``X.columns`` if available.
    sample_size:
        Maximum rows to feed into SHAP (capped for runtime).
    top_k:
        Return at most this many features in ``feature_importance``.

    Returns
    -------
    dict matching the T10 ``global_explanation`` sub-schema.
    """
    if X is None:
        return _empty_result()

    names = list(feature_names) if feature_names else _infer_feature_names(X)
    n_rows = _row_count(X)
    if n_rows == 0 or not names:
        return _empty_result()

    if model is not None:
        try:
            return _explain_shap(model, X, names, sample_size, top_k)
        except Exception as exc:
            logger.info("SHAP unavailable (%s); using variance fallback.", exc)

    return _explain_variance(X, names, top_k)


# ---------------------------------------------------------------------------
# SHAP path
# ---------------------------------------------------------------------------

def _explain_shap(  # pragma: no cover
    model: Any,
    X: Any,
    names: list[str],
    sample_size: int,
    top_k: int,
) -> dict[str, Any]:
    """Run the real shap.Explainer pipeline."""
    import shap  # type: ignore
    import numpy as np  # type: ignore

    X_sample = X.head(sample_size) if hasattr(X, "head") else X[:sample_size]
    explainer = shap.Explainer(model, X_sample)
    shap_values = explainer(X_sample)

    vals = shap_values.values
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


# ---------------------------------------------------------------------------
# Variance-based fallback (no external deps)
# ---------------------------------------------------------------------------

def _explain_variance(X: Any, names: list[str], top_k: int) -> dict[str, Any]:
    """Variance-weighted feature importance — model-free fallback."""
    importances: list[tuple[str, float]] = []
    for name in names:
        try:
            col = X[name] if hasattr(X, "__getitem__") and name in _columns_of(X) else None
            if col is None:
                continue
            numeric = [float(v) for v in col if v is not None and _is_numeric(v)]
            if len(numeric) < 2:
                importances.append((str(name), 0.0))
                continue
            mean = sum(numeric) / len(numeric)
            variance = sum((v - mean) ** 2 for v in numeric) / len(numeric)
            importances.append((str(name), float(variance ** 0.5)))
        except Exception:
            importances.append((str(name), 0.0))

    pairs = sorted(importances, key=lambda p: abs(p[1]), reverse=True)[:top_k]
    feature_importance = [
        {"feature": n, "importance": v, "rank": i + 1}
        for i, (n, v) in enumerate(pairs)
    ]
    return {
        "technique": "variance_proxy",
        "feature_importance": feature_importance,
        "sample_size": _row_count(X),
        "tool": "variance-fallback",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_count(X: Any) -> int:
    try:
        return int(len(X))
    except Exception:
        return 0


def _columns_of(X: Any) -> list[str]:
    try:
        return [str(c) for c in X.columns]
    except Exception:
        return []


def _infer_feature_names(X: Any) -> list[str]:
    cols = _columns_of(X)
    if cols:
        return cols
    try:
        ncol = X.shape[1]
        return [f"f{i}" for i in range(ncol)]
    except Exception:
        return []


def _is_numeric(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False


def _empty_result() -> dict[str, Any]:
    return {
        "technique": "none",
        "feature_importance": [],
        "sample_size": 0,
        "tool": None,
    }
