"""Final Report assembly for Phase 1."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.scope_agent.uncorroborated import uncorroborated_finding


def assemble_report(ctx: dict[str, Any], uris: dict[str, str],
                    llm_summary: str | None, prompt_note: str) -> Report:
    """Build the Phase 1 ``Report`` from the processing context.

    :param ctx: Processing context (see ``ScopeAgent.process``).
    :param uris: Stored artefact URIs keyed by template id.
    :param llm_summary: Optional LLM narrative for the report summary.
    :param prompt_note: Prompt-provenance note (recorded as a tool call).
    """
    verification_map = ctx["verification_map"]
    art43 = ctx["art43"]
    mismatches = [f for f, v in verification_map.items() if v == "mismatch"]
    return Report(
        phase_id="P1",
        artefact_uri=uris["T02_system_card"],
        summary=(
            llm_summary
            or f"Phase 1 complete. verified_risk_tier={ctx['verified_risk_tier']}, "
               f"verified_modality={ctx['verified_modality']}, "
               f"art43_procedure={art43['procedure']}, "
               f"mismatches={mismatches or 'none'}."
        ),
        confidence=0.9 if not mismatches else 0.65,
        tool_calls=[
            {"tool": "annex_iii_classify", "result": f"{len(ctx['annex_entries'])} entries"},
            {"tool": "declaration_diff", "result": verification_map},
            {"tool": "art43_select", "result": art43["procedure"]},
            {"tool": "client_doc_search", "result": f"hits={len(ctx['client_doc_hits'])}"},
            {"tool": "prompt_runtime", "result": prompt_note},
        ],
        declaration_verification_delta={
            "declaration_verification": verification_map,
            "verified_modality": ctx["verified_modality"],
            "verified_risk_tier": ctx["verified_risk_tier"],
            "annex_iii_mapping": [dict(e) for e in ctx["annex_entries"]],
            "is_llm_or_agentic": ctx["is_llm_or_agentic"],
            "art43_decision": dict(art43),
            "art43_delta": ctx["art43_delta"],
            "hitl_required": bool(mismatches),
            "hitl_reason": (f"Declaration mismatch on fields: {mismatches}"
                            if mismatches else None),
            "blocking_findings": [f for f in [uncorroborated_finding(ctx["annex_entries"])] if f],
            "phase_artefacts": {
                tid: {"uri": uri, "sha256": "", "template_id": tid}
                for tid, uri in uris.items()
            },
        },
    )
