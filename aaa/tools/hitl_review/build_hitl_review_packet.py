"""Part 4 of the former ``hitl_review`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.hitl_review.case_entry import _case_entry  # noqa: F401
from aaa.tools.hitl_review.evidence_for_case import _evidence_for_case, hitl_cases  # noqa: F401
from aaa.tools.hitl_review.tid_phase import (  # noqa: F401
    _HITL_VERDICTS,
    _TID_PHASE,
    DECISION_ACCEPT,
    DECISION_OVERRIDE,
    DECISION_UPHOLD,
    _now,
)


def build_hitl_review_packet(state: dict) -> dict[str, Any]:
    """Build the editable HITL review packet from a completed (provisional) state.

    Cases come from Verifier escalations. When the audit demands review for a
    different reason (``hitl_required`` set by an adverse verdict) and nothing
    was escalated, the material findings behind that verdict are turned into
    cases instead — so a reviewer is never told to act with nothing to act on.
    """
    from aaa.tools.hitl_review.verdict.case_entry import verdict_case_entry
    from aaa.tools.hitl_review.verdict.cases import verdict_case_findings

    escalated = hitl_cases(state)
    cases = [_case_entry(state, tid) for tid in escalated]
    if not cases and state.get("hitl_required"):
        cases = [verdict_case_entry(state, tid, findings)
                 for tid, findings in sorted(verdict_case_findings(state).items())]

    return {
        "engagement_id": state.get("engagement_id"),
        "status": "PENDING_HUMAN_REVIEW",
        "generated_at": _now(),
        "hitl_required": bool(state.get("hitl_required", False)),
        "hitl_reason": state.get("hitl_reason"),
        # Append-only; `hitl_reason` is a single string many writers assign
        # to, so an Orchestrator escalation kept only there is overwritten
        # by the next phase that closes escalate_hitl.
        "orchestrator_alerts": list(state.get("hitl_alerts") or []),
        "provisional_final_verdict": state.get("final_verdict"),
        "provisional_kpis": {
            "intake_completeness_score": state.get("intake_completeness_score"),
            "completeness_score": state.get("completeness_score"),
            "regulatory_coverage_pct": state.get("regulatory_coverage_pct"),
        },
        # What the audit noticed about its own bookkeeping. Each of these was
        # recorded by a gate and read by nobody, which is the shape of defect
        # this whole sequence has been removing one instance at a time — a fact
        # the system knows and no reader ever sees. The reviewer is the reader
        # they were always for.
        "audit_bookkeeping": {
            # Fix 26/35: artefacts the Verifier did not admit, or that a lost
            # phase never produced, with the articles each held back.
            "unadmitted_artefacts": list(state.get("unadmitted_artefacts") or []),
            # Fix 40: articles a phase's tier-agnostic contract claimed that this
            # engagement does not carry. A long list here is normal, not a defect.
            "out_of_scope_claims": list(state.get("out_of_scope_claims") or []),
            # Fix 50: articles a critique cited that the artefact is not
            # accountable for. Any entry here is a divergence worth a look.
            "over_cited_articles": list(state.get("over_cited_articles") or []),
        },
        "instructions": (
            "For each case set human_decision to one of "
            "'accept' (admit the artefact), 'uphold_escalation' (the concern stands), "
            "or 'override' (then set human_suggested_verdict to accept/accept_with_notes/"
            "rerun/escalate_hitl). Add human_rationale (and optional human_evidence_uris). "
            "Save this file, then run: python -m scripts.finalize_hitl <engagement_id>."
        ),
        "cases": cases,
    }
