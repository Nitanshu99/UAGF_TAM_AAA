"""Which metrics the model is scored with: the task the evidence shows, not a default.

``run_model_validator`` scored every model as ``decl.get("task") or "classification"``.
No dispatch carries ``task``, so a forecaster would have been scored on exact-match
accuracy and an anomaly detector on its raw ``-1/+1`` outputs. The loader's inferred
task wins, the declared Stage B ``task_type`` is next, and only an unknown task is
treated as classification.
"""
from __future__ import annotations

from typing import Any

_REGRESSION = ("regression", "forecast", "time_series", "timeseries")


def metrics_task(inferred: str, decl: dict[str, Any], stage_b: dict[str, Any]) -> str:
    """``"regression"`` or ``"classification"`` for :func:`metric_suite`.

    :param inferred: ``ScoredEvaluation.task_type`` (anomaly labels are mapped to 0/1).
    :param decl: Declaration summary (an explicit ``task`` still wins when given).
    :param stage_b: The Annex IV dossier, for its declared ``task_type``.
    """
    explicit = str(decl.get("task") or "").lower()
    if explicit:
        return explicit
    if inferred == "regression":
        return "regression"
    if inferred in ("classification", "anomaly"):
        return "classification"
    declared = str(stage_b.get("task_type") or "").lower()
    return "regression" if any(k in declared for k in _REGRESSION) else "classification"


__all__ = ["metrics_task"]
