"""Build a review case for a verdict-driven (non-escalated) artefact.

Mirrors :func:`_case_entry`'s schema exactly so ``finalize_hitl`` and
``apply_human_decisions`` need no changes — the difference is provenance:
``verdict`` is ``None`` (the Verifier did not escalate) and ``issues`` carry
the material findings that drove the adverse verdict instead.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.hitl_review.tid_phase import _TID_PHASE


def verdict_case_entry(state: dict, tid: str,
                       findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one editable review case from verdict-driven findings.

    :param state: The provisional final AuditState.
    :type state: dict
    :param tid: Template id of the artefact to review.
    :type tid: str
    :param findings: Material findings raised by that artefact's phase.
    :type findings: list[dict[str, Any]]
    :returns: Case dict with empty human-input fields, same shape as an
        escalation-driven case.
    :rtype: dict[str, Any]
    """
    from aaa.tools.hitl_review.verdict.cases import finding_articles

    ref = (state.get("phase_artefacts", {}) or {}).get(tid) or {}
    articles = sorted({a for f in findings for a in finding_articles(f)})
    return {
        "template_id": tid,
        "phase": _TID_PHASE.get(tid, "unknown"),
        "verdict": None,
        "escalation_source": "verdict",
        "artefact_uri": ref.get("uri", "") if isinstance(ref, dict) else "",
        "issues": [f"{f.get('finding_id', '')}: {f.get('description', '')}".strip(": ")
                   for f in findings],
        "article_citations": articles,
        "scores": {},
        "total_score": None,
        "evidence_uris": [ref["uri"]] if isinstance(ref, dict) and ref.get("uri") else [],
        # ── Human input — fill these, then run scripts/finalize_hitl.py ──
        "human_decision": "",
        "human_suggested_verdict": "",
        "human_rationale": "",
        "human_evidence_uris": [],
        "reviewed_by": "",
        "reviewed_at": "",
    }
