"""Recompute the model's metrics on the evaluation set and compare them with the declared ones."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.declared import unverified_declared_finding
from aaa.agents.tier2.model_validator.metrics import METRIC_MAP, diff_declared_metrics
from aaa.agents.tier2.model_validator.ranking import measure_ranking
from aaa.agents.tier2.model_validator.task import metrics_task
from aaa.tools.metric_suite import metric_suite
from aaa.tools.metric_suite.interval import bootstrap_intervals


def measure_metrics(ctx: EvalContext, decl: dict[str, Any], store: Any = None) -> dict[str, Any]:
    """Compute the task's metrics and record the declared-versus-measured findings on *ctx*.

    :param ctx: The evaluation context (scored labels, dossier, findings).
    :param decl: The declaration summary.
    :param store: Evidence store, for declared ranking metrics recomputed from the evaluation set.
    :returns: The metric-suite result.
    """
    task = metrics_task(ctx.task_type, decl, ctx.stage_b)
    metrics_result = metric_suite(y_true=ctx.y_eval, y_pred=ctx.y_pred,
                                  y_proba=ctx.y_proba, task=task,
                                  positive_label=ctx.positive_label)
    measure_ranking(store, ctx, metrics_result)
    unverified = unverified_declared_finding(
        ctx.stage_b, metrics_result,
        ctx.stage_b.get("model_access_mode") or ctx.t01b.get("model_access_mode"))
    if unverified:
        ctx.findings.append(unverified)
    if ctx.eval_scored:
        declared = ctx.stage_b.get("accuracy_metrics") or {}
        wanted = [comp for key, (comp, _label) in METRIC_MAP.items() if key in declared]
        intervals = bootstrap_intervals(list(ctx.y_eval), list(ctx.y_pred), ctx.y_proba,
                                        ctx.positive_label, wanted) if wanted else {}
        diff_findings, diff_positives = diff_declared_metrics(declared, metrics_result, intervals)
        ctx.findings.extend(diff_findings)
        ctx.positives.extend(diff_positives)
    return metrics_result
