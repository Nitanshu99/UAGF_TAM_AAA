"""The LIME tabular pipeline over the output :func:`.target.lime_target` picks."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.lime_explain.explain.instance import explain_one
from aaa.tools.lime_explain.explain.target import lime_target
from aaa.tools.lime_explain.logger import (  # noqa: F401
    _DEFAULT_NUM_FEATURES,
    _DEFAULT_NUM_INSTANCES,
    logger,
)


def _explain_lime(  # pragma: no cover
    model: Any,
    X: Any,
    names: list[str],
    class_names: Sequence[str] | None,
    num_instances: int,
    num_features: int,
) -> list[dict[str, Any]]:
    """Run the real lime.lime_tabular pipeline."""
    import numpy as np  # type: ignore
    from lime.lime_tabular import LimeTabularExplainer  # type: ignore

    X_arr = X.values if hasattr(X, "values") else np.asarray(X)
    classes = list(class_names) if class_names else None

    target = lime_target(model)
    explainer = LimeTabularExplainer(
        training_data=X_arr, feature_names=names, mode=target.mode,
        class_names=classes if target.mode == "classification" else None,
        discretize_continuous=True)

    out: list[dict[str, Any]] = []
    last_error: Exception | None = None
    n = min(num_instances, len(X_arr))
    for i in range(n):
        try:
            out.append(explain_one(explainer, target, X_arr, i, num_features, classes))
        except Exception as exc:  # noqa: BLE001 - one bad row must not sink the rest
            last_error = exc
            continue
    if not out and last_error is not None:
        # Every instance failed: raise so the caller degrades to the snapshot
        # *with a reason*, rather than returning an empty list that reads as
        # "no local explanations were requested".
        raise last_error
    return out
