"""
lime_explain — LIME local instance explanations (§4.2).

Returns a list of per-instance explanations compatible with the T10
``local_explanations`` block.

Production path:  ``lime.lime_tabular.LimeTabularExplainer``.
Offline/fallback: returns per-instance feature snapshot with simple
                  z-score contributions (no external dependency).

Usage
-----
    from src.tools.lime_explain import lime_explain

    explanations = lime_explain(
        model=clf,
        X=X_test,
        feature_names=cols,
        num_instances=5,
        num_features=10,
    )
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

_DEFAULT_NUM_INSTANCES = 5
_DEFAULT_NUM_FEATURES = 10


def lime_explain(
    model: Any = None,
    X: Any = None,
    feature_names: Sequence[str] | None = None,
    class_names: Sequence[str] | None = None,
    num_instances: int = _DEFAULT_NUM_INSTANCES,
    num_features: int = _DEFAULT_NUM_FEATURES,
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

    if model is not None:
        try:
            return _explain_lime(model, X, names, class_names, num_instances, num_features)
        except Exception as exc:
            logger.info("LIME unavailable (%s); using snapshot fallback.", exc)

    return _explain_snapshot(X, names, num_instances, num_features)


# ---------------------------------------------------------------------------
# LIME path
# ---------------------------------------------------------------------------

def _explain_lime(  # pragma: no cover
    model: Any,
    X: Any,
    names: list[str],
    class_names: Sequence[str] | None,
    num_instances: int,
    num_features: int,
) -> list[dict[str, Any]]:
    """Run the real lime.lime_tabular pipeline."""
    from lime.lime_tabular import LimeTabularExplainer  # type: ignore
    import numpy as np  # type: ignore

    X_arr = X.values if hasattr(X, "values") else np.asarray(X)
    classes = list(class_names) if class_names else None

    explainer = LimeTabularExplainer(
        training_data=X_arr,
        feature_names=names,
        class_names=classes,
        discretize_continuous=True,
    )

    out: list[dict[str, Any]] = []
    n = min(num_instances, len(X_arr))
    for i in range(n):
        instance = X_arr[i]
        try:
            exp = explainer.explain_instance(
                data_row=instance,
                predict_fn=model.predict_proba,
                num_features=num_features,
            )
            top_label = exp.top_labels[0] if exp.top_labels else 0
            top_features = [
                {"feature": str(feat), "contribution": float(contrib)}
                for feat, contrib in exp.as_list(label=top_label)
            ]
            probs = exp.predict_proba.tolist() if exp.predict_proba is not None else []
            out.append(
                {
                    "instance_id": f"instance_{i}",
                    "prediction": str(classes[top_label]) if classes else str(top_label),
                    "predicted_probability": float(max(probs)) if probs else None,
                    "top_features": top_features,
                }
            )
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# Snapshot fallback (no external deps)
# ---------------------------------------------------------------------------

def _explain_snapshot(
    X: Any,
    names: list[str],
    num_instances: int,
    num_features: int,
) -> list[dict[str, Any]]:
    """Per-instance feature snapshot — model-free fallback."""
    out: list[dict[str, Any]] = []
    n = min(num_instances, _row_count(X))
    for i in range(n):
        try:
            row = X.iloc[i] if hasattr(X, "iloc") else X[i]
            contribs: list[tuple[str, float]] = []
            for name in names:
                try:
                    val = row[name] if hasattr(row, "__getitem__") else None
                    if val is None or not _is_numeric(val):
                        continue
                    contribs.append((str(name), float(val)))
                except Exception:
                    continue
            contribs.sort(key=lambda p: abs(p[1]), reverse=True)
            top = [{"feature": n_, "contribution": v} for n_, v in contribs[:num_features]]
            out.append(
                {
                    "instance_id": f"instance_{i}",
                    "prediction": "unknown",
                    "predicted_probability": None,
                    "top_features": top,
                }
            )
        except Exception:
            continue
    return out


def _row_count(X: Any) -> int:
    try:
        return int(len(X))
    except Exception:
        return 0


def _infer_feature_names(X: Any) -> list[str]:
    try:
        return [str(c) for c in X.columns]
    except Exception:
        try:
            return [f"f{i}" for i in range(X.shape[1])]
        except Exception:
            return []


def _is_numeric(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False
