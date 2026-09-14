"""A report template's escalation is downgraded only when it is genuinely non-material."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.logger import _REPORT_TIDS, logger
from aaa.agents.tier1.verifier.issues import material_non_conformity


def downgrade_report_escalation(state: dict, tid: str, verdict: str,
                                phase_label: str) -> str:
    """Downgrade a T17/T18 escalation that carries no material non-conformity.

    A report template summarises an already-assessed state, so an escalation
    on one is editorial unless the critique also failed factual accuracy or
    named a material non-conformity. The downgrade calls itself "non-material"
    and never checked (M20); with a material non-conformity now escalating
    directly, an unchecked downgrade would re-admit on T17/T18 precisely what
    the gate refused.

    :param state: The mutable AuditState, holding ``verifier_critiques``.
    :param tid: The artefact just critiqued.
    :param verdict: The verdict as recorded.
    :param phase_label: Human-readable phase label used in the logs.
    :returns: The verdict, downgraded to ``accept_with_notes`` where that applies.
    """
    if tid not in _REPORT_TIDS or verdict != "escalate_hitl":
        return verdict
    critique = state["verifier_critiques"][tid]
    scores = critique.get("scores") or {}
    material = material_non_conformity(critique.get("issues") or [])
    if scores.get("factual_accuracy", 1) == 0 or material is not None:
        return verdict
    critique["verdict"] = "accept_with_notes"
    critique.setdefault("notes", []).append(
        "Report-template escalation downgraded to accept_with_notes "
        "(non-material; summarises an already-assessed state).")
    logger.info("%s: report-template %s escalation downgraded.", phase_label, tid)
    return "accept_with_notes"


__all__ = ["downgrade_report_escalation"]
