"""Final Report assembly for Phase 6."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION


def assemble_report(t17: dict[str, Any], t17_ref: dict[str, Any],
                    t18: dict[str, Any], t18_ref: dict[str, Any],
                    rendered: dict[str, Any], llm_summary: str | None,
                    prompt_note: str) -> Report:
    """Build the Phase 6 :class:`~aaa.agents.base.Report`.

    :param t17: T17 compliance-matrix payload.
    :param t17_ref: Stored T17 artefact reference.
    :param t18: Final T18 payload carrying the derived signing status.
    :param t18_ref: Stored T18 artefact reference.
    :param rendered: ``report_render`` output (renderer + URIs).
    :param llm_summary: Executive summary from the LLM, if any.
    :param prompt_note: Prompt-runtime provenance note.
    :returns: Report with the T18 artefact URI and the final verdict.
    """
    final_verdict = t17.get("final_verdict") or DISCLAIMER_OF_OPINION
    # F15: the flag rides on the artefact that was actually produced, so the
    # Report cannot claim a signature the T18 does not carry.
    signed = bool(t18.get("report_signed"))
    withheld = list(t18.get("signature_withheld") or [])
    return Report(
        phase_id="P6",
        artefact_uri=t18_ref["uri"],
        summary=(llm_summary
                 or f"Phase 6 complete. final_verdict={final_verdict}, "
                    f"articles={len(t17.get('articles', []))}, "
                    f"renderer={rendered.get('renderer')}."),
        confidence=0.95,
        report_signed=signed,
        tool_calls=[
            {"tool": "template_render", "result": f"T17 uri={t17_ref['uri']}"},
            {"tool": "report_render", "result": f"renderer={rendered.get('renderer')}"},
            {"tool": "template_render", "result": f"T18 uri={t18_ref['uri']}"},
            {"tool": "prompt_runtime", "result": prompt_note},
        ],
        declaration_verification_delta={
            "phase_artefacts": {
                "T17_compliance_matrix": dict(t17_ref),
                "T18_audit_report": dict(t18_ref),
            },
            "final_verdict": final_verdict,
            "auditor_opinion": t18.get("auditor_opinion"),
            "report_signed": signed,
            "signature_withheld": withheld,
        },
    )
