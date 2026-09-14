"""T18 audit-report payload builder."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.report_architect.management import management_response_shell
from aaa.agents.tier2.report_architect.opinion import auditor_opinion
from aaa.agents.tier2.report_architect.t18.inputs import t18_inputs
from aaa.agents.tier2.report_architect.t18.sections import (
    embedded_artefacts,
    executive_summary,
    kpis_section,
    metadata_section,
)


def build_t18(engagement_id: str, decl: dict[str, Any], t17_ref: dict[str, Any],
              now: str) -> dict[str, Any]:
    """Build the T18 audit report payload (before PDF rendering).

    :param engagement_id: Engagement identifier.
    :param decl: Declaration summary carrying the full engagement state.
    :param t17_ref: Stored T17 artefact reference.
    :param now: ISO-8601 generation timestamp.
    :returns: T18 audit-report dictionary with ``rendered_report`` empty.
    """
    ics, cs, rc, final_verdict, blocking_findings, positive_findings, \
        roadmap, hitl = t18_inputs(decl)
    return {
        "engagement_id": engagement_id,
        "schema_version": "1.0.0",
        "engagement_metadata": metadata_section(decl, decl.get("stage_a") or {}),
        "executive_summary": executive_summary(engagement_id, final_verdict,
                                               len(blocking_findings), ics, cs, rc),
        "kpis": kpis_section(ics, cs, rc),
        "final_verdict": final_verdict,
        "report_status": "PROVISIONAL_PENDING_HITL" if hitl else "FINAL",
        "hitl_pending": hitl,
        # F15: unsigned until `signing_status` says otherwise. A report that
        # never reaches the signing gate must not read as though it passed one.
        "report_signed": False,
        "signature_withheld": ["the signing gate has not been evaluated"],
        "auditor_opinion": auditor_opinion(decl, final_verdict),
        "art43_decision": decl.get("art43_decision"),
        "embedded_artefacts": embedded_artefacts(decl),
        "compliance_matrix_ref": dict(t17_ref),
        "blocking_findings": blocking_findings,
        "positive_findings": positive_findings,
        "remediation_roadmap": roadmap,
        "management_response": management_response_shell(
            blocking_findings + positive_findings, roadmap),
        "risk_heatmap_uri": None,
        "maturity_radar_uri": None,
        "cgsa_report_url": decl.get("cgsa_report_url"),
        "rendered_report": {"json_uri": ""},  # filled after report_render
        "hitl_required": hitl,
        "hitl_reason": decl.get("hitl_reason"),
        "verifier_summary": decl.get("verifier_summary", {}),
        "generated_at": now,
    }
