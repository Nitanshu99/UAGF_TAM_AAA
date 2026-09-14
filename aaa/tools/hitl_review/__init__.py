"""Human-in-the-loop (HITL) review packet — build + resolve.

When the audit completes with deferred HITL cases (Verifier verdict
``escalate_hitl`` on one or more artefacts), the pipeline still emits a
*provisional* report. This module produces a self-contained review packet that a
human auditor edits in place: each escalated artefact is listed with **why** it
escalated and the **evidence** that was pulled, plus empty fields for the human's
decision and rationale.

After the human fills the packet, ``apply_human_decisions`` folds those decisions
back into the audit state (admitting, upholding, or overriding each case) so the
compliance matrix + KPIs can be recomputed and a FINAL report rendered
(see ``scripts/finalize_hitl.py``).

Packet lifecycle:  PENDING_HUMAN_REVIEW  →  (human edits)  →  RESOLVED"""
from aaa.tools.hitl_review.apply_human_decisions import apply_human_decisions  # noqa: F401
from aaa.tools.hitl_review.build_hitl_review_packet import build_hitl_review_packet  # noqa: F401
from aaa.tools.hitl_review.case_entry import _case_entry  # noqa: F401
from aaa.tools.hitl_review.decision_to_verdict import (  # noqa: F401
    _apply_case,
    _decision_to_verdict,
)
from aaa.tools.hitl_review.evidence_for_case import _evidence_for_case, hitl_cases  # noqa: F401
from aaa.tools.hitl_review.tid_phase import (  # noqa: F401
    _HITL_VERDICTS,
    _TID_PHASE,
    DECISION_ACCEPT,
    DECISION_OVERRIDE,
    DECISION_UPHOLD,
    _now,
)

__all__ = [
    '_TID_PHASE', '_HITL_VERDICTS', 'DECISION_ACCEPT', 'DECISION_UPHOLD', 'DECISION_OVERRIDE',
    '_now', '_evidence_for_case', 'hitl_cases', '_case_entry', 'build_hitl_review_packet',
    '_decision_to_verdict', '_apply_case', 'apply_human_decisions', '__all__',
]
