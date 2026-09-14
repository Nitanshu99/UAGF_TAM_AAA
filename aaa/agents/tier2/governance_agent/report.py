"""Final Report assembly for Phase 5."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.governance_agent.decision import phase5_hitl
from aaa.agents.tier2.governance_agent.delta import assemble_delta
from aaa.tools.cgsa_ingest import IngestResult


def assemble_report(ctx: dict[str, Any]) -> Report:
    """Build the final Phase 5 ``Report`` from the processing context.

    :param ctx: Processing context with keys ``result``, ``payload``, ``spawn``,
        ``t14``/``t15`` (+ URIs), ``risk_tier_mismatch``, ``evidence_uris``,
        ``client_doc_hits``, ``llm_summary``, ``prompt_note``.
    :returns: The Phase 5 report with the full §5.4 state delta.
    """
    result: IngestResult = ctx["result"]
    spawn, t15 = ctx["spawn"], ctx["t15"]
    phase5_verdict = result.state_delta.get("cgsa_phase5_verdict") or "PASS_WITH_OBSERVATIONS"
    # The same decision T14 records, so the artefact and the report cannot differ.
    hitl_required, hitl_reason = phase5_hitl(result, t15, ctx["risk_tier_mismatch"])
    delta, _recon_hitl = assemble_delta(ctx, hitl_required)
    if hitl_required:
        delta["hitl_required"] = True
        delta["hitl_reason"] = hitl_reason

    return Report(
        phase_id="P5",
        artefact_uri=ctx["t14_uri"],
        summary=(
            ctx["llm_summary"]
            or f"Phase 5 complete. cgsa_phase5_verdict={phase5_verdict}, "
               f"csp_satisfiable={result.state_delta.get('cgsa_csp_satisfiable')}, "
               f"blocking_findings={len(result.state_delta.get('cgsa_blocking_findings', []))}, "
               f"low_confidence_controls={len(result.low_confidence_controls)}, "
               f"cyber_spawn={spawn['cyber_spawn']}, privacy_spawn={spawn['privacy_spawn']}."
        ),
        confidence=0.9 if not hitl_required else 0.65,
        tool_calls=[
            {"tool": "cgsa_pull",
             "result": f"assessment_id={result.payload.get('metadata', {}).get('assessment_id', 'inline')}"},
            {"tool": "cgsa_ingest",
             "result": (f"schema_errors={len(result.schema_errors)}, "
                        f"phase5_verdict={phase5_verdict}, "
                        f"risk_tier_match={result.state_delta.get('cgsa_risk_tier_match')}")},
            {"tool": "client_doc_search", "result": f"hits={len(ctx['client_doc_hits'])}"},
            {"tool": "prompt_runtime", "result": ctx["prompt_note"]},
        ],
        declaration_verification_delta=delta,
    )
