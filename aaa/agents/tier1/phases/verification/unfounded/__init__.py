"""An escalation whose every material defect is shown unfounded does not block admission.

A Verifier escalation on a material artefact defect keeps the artefact out of the
evidence. Two kinds of material defect can be shown wrong from what the runtime already
holds: one naming a field the template does not define (:mod:`.uncontracted`), and one
disputing a membership statement the engagement's ``binding_articles`` confirm
(:mod:`.scope`). When every material defect is one of these, the artefact is admitted
with each reason recorded; one defect without such a reason keeps the escalation, and a
``factual_accuracy`` of 0 is never downgraded.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.logger import logger
from aaa.agents.tier1.phases.verification.unfounded.scope import scope_refuted_reason
from aaa.agents.tier1.phases.verification.unfounded.uncontracted import uncontracted_reason
from aaa.agents.tier1.verifier.issues import is_defect


def _material_defects(critique: dict[str, Any]) -> list[dict[str, Any]]:
    return [i for i in critique.get("issues") or [] if isinstance(i, dict) and is_defect(i)
            and str(i.get("materiality", "")).lower() == "material"]


def downgrade_unfounded_escalation(state: dict, tid: str, verdict: str, phase_label: str,
                                   content: Any = None) -> str:
    """Admit *tid* when every material defect behind its escalation is unfounded.

    :param state: The mutable AuditState, holding ``verifier_critiques``.
    :param tid: The artefact just critiqued.
    :param verdict: The verdict as recorded.
    :param phase_label: Human-readable phase label used in the logs.
    :param content: The artefact the Verifier reviewed.
    :returns: The verdict, ``accept_with_notes`` where no material defect stood.
    """
    critique = state["verifier_critiques"][tid]
    defects = _material_defects(critique)
    if (verdict != "escalate_hitl" or not defects
            or (critique.get("scores") or {}).get("factual_accuracy", 1) == 0):
        return verdict
    reasons = [uncontracted_reason(i, tid) or scope_refuted_reason(i, content, state)
               for i in defects]
    if None in reasons:
        return verdict
    critique["verdict"] = "accept_with_notes"
    critique.setdefault("notes", []).extend(
        f"Material issue on {i.get('field') or 'the artefact'} set aside: {r}. The artefact is "
        "admitted with the issue recorded." for i, r in zip(defects, reasons))
    logger.info("%s: %s escalation rested only on unfounded issues; admitted.", phase_label, tid)
    return "accept_with_notes"


__all__ = ["downgrade_unfounded_escalation"]
