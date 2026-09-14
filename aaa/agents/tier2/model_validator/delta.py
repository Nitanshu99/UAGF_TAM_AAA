"""Verification-delta assembly for the Phase 3 report."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext, LlmSynthesis
from aaa.platform.audit_programme import outcome
from aaa.tools.findings import backfill_finding_evidence, collect_evidence_uris


def build_delta(message: dict[str, Any], ctx: EvalContext, uris: dict[str, str],
                t11: dict[str, Any], llm: LlmSynthesis) -> dict[str, Any]:
    """Assemble the ``declaration_verification_delta`` for the Report.

    :param message: Original dispatch message.
    :param ctx: Evaluation context with findings and insufficiency flags.
    :param uris: Stored artefact URIs keyed by template id.
    :param t11: T11 robustness-report content.
    :param llm: LLM synthesis outcome (for evidence backfill sources).
    :returns: Delta dictionary including any HITL escalation.
    """
    delta: dict[str, Any] = {"phase_artefacts": {
        template_id: {"uri": uri, "sha256": "", "template_id": template_id}
        for template_id, uri in uris.items()}}
    evidence_pool = collect_evidence_uris(
        message.get("evidence_uris", []), llm.client_doc_hits, list(uris.values()))
    backfill_finding_evidence(ctx.findings, evidence_pool)
    backfill_finding_evidence(ctx.positives, evidence_pool)
    if ctx.findings:
        delta["blocking_findings"] = ctx.findings
    if ctx.positives:
        delta["positive_findings"] = ctx.positives
    if ctx.insufficient:
        delta["insufficient_evidence_articles"] = sorted(ctx.insufficient)
    delta["procedure_outcomes"] = {
        **outcome("metric_suite", ctx.eval_scored,
                  "no system predictions and ground-truth labels to recompute metrics on"),
        **outcome("robustness_probe", t11.get("overall_robustness_verdict") != "NOT_TESTED",
                  t11.get("skipped_reason")),
        **({} if ctx.ranking is None else outcome(
            "ranking_metrics", bool(ctx.ranking.get("metrics")), ctx.ranking.get("reason")))}
    material = any(f.get("materiality") == "material" for f in ctx.findings)
    if not (material or ctx.insufficient):
        return delta
    reasons = []
    if t11["overall_robustness_verdict"] == "FAIL":
        reasons.append("robustness verdict FAIL (min_adversarial_accuracy="
                       f"{t11.get('min_adversarial_accuracy')})")
    if material:
        reasons.append("material model-validation finding(s) raised")
    if ctx.insufficient:
        reasons.append("model/eval artefacts could not be independently verified: "
                       + ", ".join(sorted(ctx.insufficient)))
    delta["hitl_required"] = True
    delta["hitl_reason"] = "Phase 3 — " + "; ".join(reasons) + "."
    return delta
