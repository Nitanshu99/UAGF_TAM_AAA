"""The overview payload and the deterministic overview written when the model is unreachable."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.client_brief.declaration import cgsa_strengths, provider_declaration


def _unassessed_articles(state: dict[str, Any]) -> list[str]:
    """Articles the audit could not assess, as the compliance matrix decided.

    ``insufficient_evidence_articles`` is an input to the verdict ladder, where a
    material finding outranks insufficient evidence; presented raw, it told the
    customer Art. 10, 13 and 15 could not be checked while the matrix rated them
    FAIL (T-20260913-031). The raw set is used only when there is no matrix.
    """
    matrix = state.get("compliance_matrix") or {}
    if matrix:
        return [article for article, verdict in matrix.items()
                if verdict == "INSUFFICIENT_EVIDENCE"]
    return list(state.get("insufficient_evidence_articles") or [])


def _overview_payload(state: dict[str, Any], sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Assemble the evidence the overview is written from."""
    return {
        "task": "Write the opening of a plain-language compliance brief for the "
                "customer: why the audit reached this verdict, what is already "
                "working, and what to fix first.",
        "final_verdict": state.get("final_verdict"),
        "auditor_opinion": state.get("auditor_opinion") or {},
        "compliance_matrix": state.get("compliance_matrix") or {},
        "provider_declaration": provider_declaration(state),
        "governance_strengths": cgsa_strengths(state),
        "remediation_roadmap": state.get("remediation_roadmap") or [],
        "articles_that_could_not_be_checked": _unassessed_articles(state),
        "article_headlines": [{"article": s["article"], "verdict": s["verdict"],
                               "headline": s.get("headline")} for s in sections],
    }
def deterministic_overview(state: dict[str, Any]) -> dict[str, Any]:
    """Build the overview from state alone, with no LLM call."""
    opinion = state.get("auditor_opinion") or {}
    return {
        "overall_explanation": " ".join(
            p for p in (opinion.get("opinion_paragraph"), opinion.get("basis_paragraph")) if p),
        "what_is_working_well": [f"{c['control_name']} — {c['finding']}"
                                 for c in cgsa_strengths(state)],
        "top_priorities": [r.get("recommended_action")
                           for r in (state.get("remediation_roadmap") or [])
                           if r.get("recommended_action")],
        "llm_written": False,
    }


__all__ = ["_overview_payload", "deterministic_overview"]
