"""Part 3 of the former ``hitl_review`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.platform.state.artefact_keys import base_template_id
from aaa.tools.hitl_review.evidence_for_case import _evidence_for_case, hitl_cases  # noqa: F401
from aaa.tools.hitl_review.tid_phase import (  # noqa: F401
    _HITL_VERDICTS,
    _TID_PHASE,
    DECISION_ACCEPT,
    DECISION_OVERRIDE,
    DECISION_UPHOLD,
    _now,
)


def _case_entry(state: dict, tid: str) -> dict[str, Any]:
    """Build one editable review case for template *tid*.

    :param state: The provisional final AuditState.
    :param tid: Template id of the escalated artefact.
    :returns: Case dict with empty human-input fields to be filled offline.
    """
    crit = (state.get("verifier_critiques", {}) or {}).get(tid, {}) or {}
    ref = (state.get("phase_artefacts", {}) or {}).get(tid) or {}
    return {
        "template_id": tid,
        # A tier-3 spawn's artefact is keyed `<template_id>@<spawn>` (P5); its
        # phase is the template's, not "unknown".
        "phase": _TID_PHASE.get(tid) or _TID_PHASE.get(base_template_id(tid), "unknown"),
        "verdict": crit.get("verdict"),
        "artefact_uri": ref.get("uri", "") if isinstance(ref, dict) else "",
        "issues": list(crit.get("issues", []) or []),
        "article_citations": list(crit.get("article_citations", []) or []),
        "scores": dict(crit.get("scores", {}) or {}),
        "total_score": crit.get("total_score"),
        "evidence_uris": _evidence_for_case(state, tid, crit),
        # ── Human input — fill these, then run scripts/finalize_hitl.py ──
        "human_decision": "",          # accept | uphold_escalation | override
        "human_suggested_verdict": "",  # required if human_decision == override
        "human_rationale": "",
        "human_evidence_uris": [],
        "reviewed_by": "",
        "reviewed_at": "",
    }
