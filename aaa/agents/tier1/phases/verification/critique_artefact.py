"""Critique one artefact with the real Verifier and record what it said."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.downgrade import downgrade_report_escalation
from aaa.agents.tier1.phases.verification.logger import (
    _REPORT_TIDS,
    _artefact_content,
    _artefact_uri,
    logger,
)
from aaa.agents.tier1.phases.verification.merge_critique import _merge_critique
from aaa.agents.tier1.phases.verification.scope_context import with_engagement_scope
from aaa.agents.tier1.phases.verification.sources import review_evidence_uris
from aaa.agents.tier1.phases.verification.unfounded import downgrade_unfounded_escalation
from aaa.agents.tier1.verifier import Verifier
from aaa.agents.tier1.verifier.verdicts import UNVERIFIED


async def _critique_artefact(verifier: Verifier, agent: Any, state: dict, tid: str,
                             articles: list[str], phase_label: str, confidence: float,
                             *, phase_id: str, evidence_uris: list[str],
                             rerun_count: int, declaration_summary: dict) -> str:
    """Critique one artefact, record the critique, and return its verdict.

    A Verifier crash records ``unverified`` (never silent, and never an
    admission — the critique did not happen); a report-template escalation
    without a factual-accuracy failure is downgraded (it summarises an
    already-assessed state), and so is one whose material defects are all
    shown unfounded.
    """
    content = _artefact_content(agent.store, state, tid)
    try:
        crit = await verifier.process({
            "phase_id": phase_id,
            "template_id": tid,
            "content": content,
            # Plus the model and datasets the phase computed from (T-20260913-076).
            "evidence_uris": review_evidence_uris({"evidence_uris": evidence_uris,
                                                   "declaration_summary": declaration_summary}),
            "rerun_count": rerun_count,
            "artefact_uri": _artefact_uri(state, tid),
            "declaration_summary": with_engagement_scope(declaration_summary, state, phase_id),
        })
    except Exception as exc:  # noqa: BLE001 - verifier failure must not pass silently
        logger.warning("Verifier failed for %s (%s); recording unverified.", tid, exc)
        crit = {"verdict": UNVERIFIED, "issues": [],
                "notes": [f"Verifier unavailable: {exc}. This artefact is "
                          f"unverified, not accepted."],
                "llm_fallback_mode": True,
                "unverified_reason": f"{type(exc).__name__}: {exc}"[:200]}
    state["verifier_critiques"][tid] = _merge_critique(crit, articles, phase_label, confidence)
    verdict = state["verifier_critiques"][tid]["verdict"]
    verdict = downgrade_report_escalation(state, tid, verdict, phase_label)
    verdict = downgrade_unfounded_escalation(state, tid, verdict, phase_label, content)
    logger.info("%s: Verifier verdict '%s' on %s.", phase_label, verdict, tid)
    return verdict


__all__ = ["_REPORT_TIDS", "_critique_artefact"]
