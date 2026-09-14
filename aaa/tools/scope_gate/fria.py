"""Whether Art. 27 obliges the audited entity to perform a fundamental-rights impact assessment.

Art. 27(1): "Prior to deploying a high-risk AI system referred to in Article 6(2), with
the exception of high-risk AI systems intended to be used in the area listed in point 2
of Annex III, deployers that are bodies governed by public law, or are private entities
providing public services, and deployers of high-risk AI systems referred to in points
5 (b) and (c) of Annex III, shall perform an assessment ...".

The gate raised the duty on a public body with a high-risk tier alone, so case 03 —
critical infrastructure, Annex III point 2 — was audited against Art. 27 and reported
it "could not be checked" (MiniMax run, 2026-09-14). The intake records Annex III
areas without their sub-points, so the 5 (b)/(c) limb cannot be read from it and is not
guessed at; the public-body limb is decided exactly.
"""
from __future__ import annotations

from typing import Any

#: Annex III area Art. 27(1) excepts: critical infrastructure.
EXCEPTED_AREA = "2"


def fria_reason(stage_a: dict[str, Any]) -> tuple[bool, str | None]:
    """Whether the FRIA duty applies, and the one-line reason when the tier suggested it would.

    :param stage_a: Stage A payload.
    :returns: ``(applies, reason)``; ``reason`` is ``None`` when the question never arose.
    """
    if not (stage_a.get("is_public_body_or_public_service")
            and stage_a.get("declared_risk_tier") == "high"):
        return False, None
    areas = {str(a) for a in stage_a.get("declared_annex_iii_sections") or []}
    if areas and areas <= {EXCEPTED_AREA}:
        return False, ("Public body / public service + high risk, but the system is used only in "
                       "Annex III point 2 (critical infrastructure), which Art. 27(1) excepts: "
                       "no FRIA duty.")
    entity = {str(e) for e in stage_a.get("entity_type") or []}
    if entity and "deployer" not in entity:
        return False, ("Public body / public service + high risk, but the audited entity is not "
                       "a deployer; the Art. 27 FRIA is the deployer's duty.")
    return True, ("Public-law body / public service + high-risk system → Art. 27 FRIA "
                  "required (FLI-R5).")


__all__ = ["EXCEPTED_AREA", "fria_reason"]
