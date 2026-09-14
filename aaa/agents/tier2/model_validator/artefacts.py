"""Building and storing the Phase 3 artefacts (T09 / T10 / T11)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext, Explainability, LlmSynthesis
from aaa.agents.tier2.model_validator.declared import declared_metrics
from aaa.agents.tier2.model_validator.t09 import build_t09
from aaa.agents.tier2.model_validator.t10 import build_t10
from aaa.agents.tier2.model_validator.t11 import build_t11
from aaa.tools.regulatory_coverage.binding_notes import annotate_non_binding


def build_and_store_artefacts(
    agent: Any,
    engagement_id: str,
    modality: str,
    ctx: EvalContext,
    metrics_result: dict[str, Any],
    expl: Explainability,
    robustness_result: dict[str, Any],
    llm: LlmSynthesis,
    t09_found: dict[str, Any] | None = None,
    risk_tier: str | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Build T09 / T10 / T11, annotate them, and write to the Evidence Store.

    :param agent: The calling :class:`ModelValidator` instance.
    :param engagement_id: Engagement identifier.
    :param modality: Normalised system modality.
    :param ctx: Resolved model / evaluation inputs.
    :param metrics_result: Output of ``metric_suite``.
    :param expl: Explainability evidence from step 3.
    :param robustness_result: Output of ``robustness_probe``.
    :param llm: LLM synthesis outcome (summary + prompt note).
    :param t09_found: Grounded document answers for the model card.
    :returns: ``(uris, t11)`` — artefact URIs keyed by template id, and the
        T11 content needed for the robustness verdict downstream.
    """
    now = datetime.now(timezone.utc).isoformat()
    t09 = build_t09(engagement_id, ctx.t01a, ctx.t01b, modality, metrics_result, now,
                    declared=declared_metrics(ctx.stage_b or ctx.t01b), found=t09_found,
                    model=ctx.model)
    t10 = build_t10(engagement_id, modality, expl, now)
    t11 = build_t11(engagement_id, modality, robustness_result, now)
    t09["art13_compliance_notes"] = (
        f"{t09['art13_compliance_notes']} {llm.prompt_note}".strip())
    t10["interpretation"] = f"{t10['interpretation']} {llm.prompt_note}".strip()
    # A measurement narrative is built from this artefact's own fields. The LLM's
    # reply summarises the whole phase and quoted numbers the artefact does not hold —
    # T11 carried metric-suite accuracy and SHAP values beside its probe fields, and
    # the Verifier refused it (case 03, T-20260913-067). It stays the Report summary.
    t11["robustness_narrative"] = f"{t11['robustness_narrative']} {llm.prompt_note}".strip()
    for payload in (t09, t10, t11):
        annotate_non_binding(payload, risk_tier)
    uris = {
        template_id: agent.store.store_artefact(
            engagement_id, "phase_3", template_id, content, agent.name)
        for template_id, content in (("T09_model_card", t09),
                                     ("T10_explainability_report", t10),
                                     ("T11_robustness_report", t11))
    }
    return uris, t11
