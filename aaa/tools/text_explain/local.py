"""Per-instance token contributions for a vectorizer + linear text pipeline (T10 local).

T10 for case 05's TF-IDF + logistic-regression CV screener carried global token
importances and no local explanation at all, because the NLP route stopped there
(T-20260913-098). For a linear model over a vectorizer the explanation of one
decision is exact, not approximated: the decision score is the intercept plus, for
every token in the instance, its vectorized weight times its coefficient.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.lime_explain.logger import _DEFAULT_NUM_FEATURES, _DEFAULT_NUM_INSTANCES
from aaa.tools.text_explain.core import linear_head


def _weights(clf: Any, prediction: Any) -> tuple[Any, str]:
    """The coefficient row behind *prediction*'s score, and what that score is."""
    import numpy as np  # type: ignore

    coef, classes = np.asarray(clf.coef_), list(clf.classes_)
    if coef.shape[0] == 1:
        return coef[0], f"decision score (log-odds) for class {classes[-1]}"
    return coef[classes.index(prediction)], f"decision score for class {prediction}"


def _instance(i: int, z: Any, names: list[str], clf: Any, prediction: Any,
              probability: float | None, num_features: int) -> dict[str, Any]:
    """One T10 local-explanation item from a vectorized row."""
    import numpy as np  # type: ignore

    weights, output = _weights(clf, prediction)
    contrib = np.asarray(z.toarray() if hasattr(z, "toarray") else z).ravel() * weights
    top = [j for j in np.argsort(-np.abs(contrib)) if contrib[j] != 0][:num_features]
    return {"instance_id": f"instance_{i}", "prediction": str(prediction),
            "predicted_probability": probability,
            "top_features": [{"feature": names[j], "contribution": float(contrib[j])}
                             for j in top],
            "explained_output": output}


def token_contributions(model: Any = None, X: Any = None,
                        num_instances: int = _DEFAULT_NUM_INSTANCES,
                        num_features: int = _DEFAULT_NUM_FEATURES,
                        reasons: list[str] | None = None) -> list[dict[str, Any]]:
    """Explain the first *num_instances* rows of *X* — the rows LIME would take.

    :param model: Fitted sklearn Pipeline whose last step is a linear classifier.
    :param X: The model's input rows (a frame holding the text column).
    :param num_instances: Rows explained.
    :param num_features: Tokens reported per row, by absolute contribution.
    :param reasons: Collects why nothing could be explained.
    :returns: T10 ``local_explanations`` items; ``[]`` when the model is not that shape.
    """
    try:
        transform, clf, names = linear_head(model)
        rows = X.iloc[:num_instances] if hasattr(X, "iloc") else X[:num_instances]
        vectors, predictions = transform.transform(rows), model.predict(rows)
        proba = model.predict_proba(rows) if hasattr(model, "predict_proba") else None
        return [_instance(i, vectors[i], names, clf, predictions[i],
                          float(max(proba[i])) if proba is not None else None, num_features)
                for i in range(len(predictions))]
    except Exception as exc:  # noqa: BLE001 - any shape it cannot read explains nothing
        if reasons is not None:
            reasons.append(f"token contributions not computed: {exc}")
        return []


__all__ = ["token_contributions"]
