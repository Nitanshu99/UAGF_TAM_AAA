"""Run the model validator phase and file its artefacts."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch, Report
from aaa.agents.tier2.common import load_intake
from aaa.agents.tier2.model_validator.artefacts import build_and_store_artefacts
from aaa.agents.tier2.model_validator.delta import build_delta
from aaa.agents.tier2.model_validator.documents import t09_evidence
from aaa.agents.tier2.model_validator.explainability import run_explainability
from aaa.agents.tier2.model_validator.inputs import build_eval_context
from aaa.agents.tier2.model_validator.llm import run_llm_synthesis
from aaa.agents.tier2.model_validator.measure import measure_metrics
from aaa.agents.tier2.model_validator.report import assemble_report
from aaa.agents.tier2.model_validator.unevidenced import append_robustness_finding, flag_unevidenced
from aaa.tools.robustness_probe import robustness_probe


async def run_model_validator(agent: Any, message: Dispatch) -> Report:
    """Run the model validator phase and file its artefacts.

    :param agent: The agent making the call and holding the evidence store.
    :param message: The dispatch to act on.
    :returns: The phase Report.
    """
    decl = message.get("declaration_summary", {})
    engagement_id: str = decl.get("engagement_id") or message["phase_id"]
    modality: str = (decl.get("modality") or "tabular").lower()

    t01a, t01b = load_intake(agent.store, message.get("evidence_uris", []))
    ctx = build_eval_context(agent.store, decl, t01a, t01b, modality)
    metrics_result = measure_metrics(ctx, decl, agent.store)
    expl = run_explainability(decl, modality, ctx)
    robustness_result = robustness_probe(
        model=ctx.model, X=ctx.x_probe, y_true=ctx.y_eval, modality=modality,
        predict_fn=ctx.predict_fn, categorical_features=ctx.categorical_features,
        declared=(ctx.stage_b or ctx.t01b).get("robustness_metrics"))
    flag_unevidenced(ctx, modality, expl, robustness_result)
    # dict() casts: pyright will not assign the Dispatch TypedDict to dict.
    llm = await run_llm_synthesis(agent, dict(message), decl, engagement_id,
                                  metrics_result, expl, robustness_result)
    uris, t11 = build_and_store_artefacts(agent, engagement_id, modality, ctx,
                                          metrics_result, expl, robustness_result, llm,
                                          t09_evidence(decl, engagement_id, ctx), decl.get("risk_tier"))
    append_robustness_finding(ctx, t11, uris["T11_robustness_report"])
    delta = build_delta(dict(message), ctx, uris, t11, llm)
    return assemble_report(uris, delta, metrics_result, expl,
                           robustness_result, llm)


__all__ = ["run_model_validator"]
