"""A model's configured hyperparameters and, where the notion is defined, its parameter count."""
from __future__ import annotations

from typing import Any

_PRIMITIVE = (str, int, float, bool, type(None))


def final_estimator(model: Any) -> Any:
    """The last step of a scikit-learn ``Pipeline``, or the model itself."""
    steps = getattr(model, "steps", None)
    return steps[-1][1] if isinstance(steps, list) and steps else model


def hyperparameters(model: Any) -> dict[str, Any] | None:
    """The estimator's own ``get_params(deep=False)``, objects named by their type.

    :param model: A loaded model.
    :returns: Parameter name → value, or ``None`` when the model exposes none.
    """
    estimator = final_estimator(model)
    if not callable(getattr(estimator, "get_params", None)):
        return None
    try:
        params: dict[str, Any] = dict(estimator.get_params(deep=False))
    except Exception:  # noqa: BLE001 — a model that cannot report its params reports none
        return None
    return {str(k): v if isinstance(v, _PRIMITIVE) else type(v).__name__ for k, v in params.items()}


def parameter_count(model: Any) -> int | None:
    """Trainable parameters where the count is well defined: torch modules, linear models.

    A tree ensemble has no agreed parameter count, so it gets ``None`` rather than
    a node tally presented as one.

    :param model: A loaded model.
    """
    if callable(getattr(model, "parameters", None)) and hasattr(model, "forward"):
        return int(sum(p.numel() for p in model.parameters()))
    estimator = final_estimator(model)
    coef = getattr(estimator, "coef_", None)
    if coef is None:
        return None
    intercept = getattr(estimator, "intercept_", None)
    return int(getattr(coef, "size", 0)) + int(getattr(intercept, "size", 0) if intercept is not None else 0)
