"""Global token-importance extraction for NLP model pipelines.

SHAP/LIME have no text handling here, so T10 for NLP systems used to degrade
to ``technique: none``. For the common traditional-NLP shape — an sklearn
Pipeline containing a fitted vectorizer (TF-IDF / count, possibly inside a
ColumnTransformer) and a linear classifier — the |coefficient| per vocabulary
token is a faithful global importance. Output matches the T10
``global_explanation`` sub-schema exactly as ``shap_explain`` produces it.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_TOP_K = 20


def _find_components(model: Any) -> tuple[Any, Any]:
    """Locate the fitted vectorizer and linear classifier inside *model*.

    :param model: Candidate sklearn ``Pipeline``.
    :type model: Any
    :returns: ``(vectorizer, classifier)`` — the first step exposing
        ``get_feature_names_out`` (without ``coef_``) and the first exposing
        ``coef_``.
    :rtype: tuple[Any, Any]
    :raises TypeError: If *model* has no ``named_steps`` (not a Pipeline).
    :raises ValueError: If no vectorizer + linear classifier pair is found.
    """
    steps = getattr(model, "named_steps", None)
    if steps is None:
        raise TypeError("model is not an sklearn Pipeline")
    vec = next((s for s in steps.values()
                if hasattr(s, "get_feature_names_out") and not hasattr(s, "coef_")), None)
    clf = next((s for s in steps.values() if hasattr(s, "coef_")), None)
    if vec is None or clf is None:
        raise ValueError("pipeline lacks a vectorizer + linear classifier pair")
    return vec, clf


def linear_head(model: Any) -> tuple[Any, Any, list[str]]:
    """Split a text pipeline into its input transform, final linear step and feature names.

    :param model: Fitted sklearn Pipeline.
    :returns: ``(everything but the last step, the linear classifier, token names)``.
    :raises ValueError: If the last step is not the pipeline's linear classifier.
    """
    _vec, clf = _find_components(model)
    if model.steps[-1][1] is not clf:
        raise ValueError("the linear classifier is not the pipeline's final step")
    transform = model[:-1]
    names = [str(n).rsplit("__", 1)[-1] for n in transform.get_feature_names_out()]
    return transform, clf, names


def token_importance(model: Any = None, top_k: int = _DEFAULT_TOP_K) -> dict[str, Any]:
    """Extract |coef|-ranked global token importances from an NLP pipeline.

    :param model: Fitted sklearn Pipeline (vectorizer + linear classifier).
    :type model: Any
    :param top_k: Maximum number of tokens returned.
    :type top_k: int
    :returns: Dict matching the T10 ``global_explanation`` sub-schema;
        ``technique: none`` when the pipeline shape is unsupported.
    :rtype: dict[str, Any]
    """
    try:
        vec, clf = _find_components(model)
        import numpy as np  # type: ignore
        names = [str(n).rsplit("__", 1)[-1] for n in vec.get_feature_names_out()]
        weights = np.abs(np.asarray(clf.coef_))
        weights = weights.mean(axis=0) if weights.ndim > 1 else weights
        order = np.argsort(weights)[::-1][:top_k]
        return {
            "technique": "token_importance",
            "feature_importance": [
                {"feature": names[i], "importance": float(weights[i]), "rank": r + 1}
                for r, i in enumerate(order)],
            # Coefficients sample no instance: None, not the vocabulary size, which
            # read as 742 records explained against a 240-record corpus (T-20260913-106).
            "sample_size": None,
            "tool": "text_explain",
            "vocabulary_size": int(len(names)),  # diagnostic, stripped from T10
        }
    except Exception as exc:  # mirror shap_explain's fail-soft contract
        logger.info("token importance unavailable (%s); returning empty result.", exc)
        # None: nothing was explained (T-20260913-039).
        return {"technique": "none", "feature_importance": [], "sample_size": None, "tool": None}
