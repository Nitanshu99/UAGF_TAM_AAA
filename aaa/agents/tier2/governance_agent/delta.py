"""State-delta assembly for the Phase 5 report."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.reconcile import reconcile_cgsa
from aaa.tools.cgsa_ingest import IngestResult
from aaa.tools.findings import backfill_finding_evidence, collect_evidence_uris


def assemble_delta(ctx: dict[str, Any], hitl_required: bool) -> tuple[dict[str, Any], bool]:
    """Build the state delta and apply reconciliation findings + spawn flags."""
    result: IngestResult = ctx["result"]
    spawn = ctx["spawn"]
    delta: dict[str, Any] = dict(result.state_delta)
    delta["phase_artefacts"] = {
        "T14_governance_findings": {
            "uri": ctx["t14_uri"], "sha256": "", "template_id": "T14_governance_findings"},
        "T15_monitoring_logging_review": {
            "uri": ctx["t15_uri"], "sha256": "", "template_id": "T15_monitoring_logging_review"},
    }
    # Treat the client's CGSA self-assessment as a claim to be tested, not as
    # evidence: reconcile its internal consistency and raise findings on gaps.
    recon_findings = reconcile_cgsa(ctx["payload"])
    if recon_findings:
        evidence_pool = collect_evidence_uris(
            ctx["evidence_uris"], ctx["client_doc_hits"], [ctx["t14_uri"], ctx["t15_uri"]])
        backfill_finding_evidence(recon_findings, evidence_pool)
        delta["blocking_findings"] = recon_findings
        hitl_required = hitl_required or any(
            f.get("materiality") == "material" for f in recon_findings)
    if spawn["cyber_spawn"]:
        delta["spawn_cyber_subagent"] = True
        delta["cyber_spawn_rationale"] = spawn["cyber_rationale"]
    if spawn["privacy_spawn"]:
        delta["spawn_privacy_subagent"] = True
        delta["privacy_spawn_rationale"] = spawn["privacy_rationale"]
    return delta, hitl_required
