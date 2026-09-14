"""Phase 3's recomputation of declared ranking metrics from the evaluation set's ranked rows.

A ranking case declared precision@k and NDCG@k and supplied no model, so the declared
figures stayed unverified — although its evaluation set records the system's rank per
query and a human relevance decision on each row (T-20260914-029). With the
ranking columns declared, the figures are reproduced and judged against query-level
intervals exactly as classification metrics are.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.metrics import diff_declared_metrics
from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.tools.ranking_metrics import NAME, ranking_metrics


def _frame(store: Any, ctx: EvalContext) -> Any:
    """The evaluation set, or ``None`` when it is not supplied or cannot be read."""
    uri = ctx.t01b.get("evaluation_dataset_uri") or ctx.stage_b.get("evaluation_dataset_uri")
    try:
        return load_artifact_from_uri(uri, store, "csv") if uri else None
    except ArtifactUnavailable:
        return None


def measure_ranking(store: Any, ctx: EvalContext, metrics_result: dict[str, Any]) -> None:
    """Recompute the declared ranking metrics and merge them into *metrics_result*, in place.

    :param store: Evidence store the evaluation set is loaded from.
    :param ctx: Evaluation context; findings, positives and insufficiency updated.
    :param metrics_result: ``metric_suite`` output, extended with ``ranking``.
    """
    dictionary = ctx.stage_b.get("data_dictionary") or ctx.t01b.get("data_dictionary") or {}
    declared = ctx.stage_b.get("accuracy_metrics") or {}
    names = [n for n in declared if NAME.fullmatch(n)]
    if not dictionary.get("ranking") or not names:
        return
    frame = _frame(store, ctx)
    result = (ranking_metrics(frame, dictionary["ranking"], dictionary.get("target_column"),
                              dictionary.get("positive_label"), names) if frame is not None
              else {"computed": False, "reason": "the evaluation set could not be loaded",
                    "metrics": {}, "intervals": {}})
    metrics_result["ranking"] = ctx.ranking = result
    if not result["metrics"]:
        return
    metrics_result.setdefault("metrics", {}).update(result["metrics"])
    if metrics_result.get("primary_metric_value") is None:
        primary = names[0] if names[0] in result["metrics"] else next(iter(result["metrics"]))
        metrics_result.update(primary_metric=primary, primary_metric_value=result["metrics"][primary],
                              evaluation_sample_size=result["n_rows"],
                              metric_suite_tool="ranking_metrics")
    found, positives = diff_declared_metrics(
        declared, metrics_result, result["intervals"],
        mapping={n: (n, n.replace("_at_", "@")) for n in result["metrics"]}, targets=False)
    ctx.findings.extend(found)
    ctx.positives.extend(positives)
    ctx.insufficient.discard("Art.15§1")


__all__ = ["measure_ranking"]
