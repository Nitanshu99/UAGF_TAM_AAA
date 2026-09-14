"""Escalation report builder for Phase 5 evidence-availability failures."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.governance_agent.errors import GOVERNANCE_INSUFFICIENT_ARTICLES

logger = logging.getLogger(__name__)


def escalate_report(
    engagement_id: str, reason: str, details: dict[str, Any] | None = None,
) -> Report:
    """Build a Report that flips Phase 5 into HITL escalation.

    A failure to *retrieve or validate* the CGSA self-assessment (pull failed,
    no fixture, service down, schema invalid) is an evidence-availability
    problem — it does **not** establish that governance is non-conformant.
    The governance articles are marked INSUFFICIENT_EVIDENCE (the compliance
    matrix downgrades the opinion to a disclaimer for them) instead of forcing
    ``cgsa_phase5_verdict="FAIL"``.  A genuine FAIL is only ever raised from a
    CGSA payload that is present *and* reports failure (see ``cgsa_ingest``).

    :param engagement_id: Engagement identifier (unused in the payload today).
    :param reason: Human-readable escalation reason.
    :param details: Optional structured error details.
    :returns: HITL-escalation ``Report`` for phase P5.
    """
    del engagement_id  # reserved: escalation reports are engagement-agnostic
    logger.warning("[GovernanceAgent] escalating: %s (%s)", reason, details)
    delta: dict[str, Any] = {
        "hitl_required": True,
        "hitl_reason": reason,
        "insufficient_evidence_articles": list(GOVERNANCE_INSUFFICIENT_ARTICLES),
        "phase_artefacts": {},
    }
    if details:
        delta["cgsa_ingest_details"] = details
    return Report(
        phase_id="P5",
        artefact_uri="",
        summary=(
            f"Phase 5 escalated to HITL — {reason}. CGSA self-assessment "
            "unavailable; governance articles (Art.9/Art.12/Art.17/Art.72) "
            "marked INSUFFICIENT_EVIDENCE (disclaimer), not FAIL."
        ),
        confidence=0.2,
        tool_calls=[{"tool": "cgsa_pull_or_ingest", "result": reason}],
        declaration_verification_delta=delta,
    )
