"""A remediation step for every finding the audit raised — finding Q17.

``remediation_roadmap`` was populated from one source: the CGSA partner payload
(§5.4). The audit's own findings never reached it, so the delivered report told
the client *"Three blocking findings require remediation before deployment"* and
then rendered no roadmap at all, because the governance partner happened to have
supplied none.

Every finding already carries a ``recommendation``. Turning that into a dated,
owned step is what a roadmap *is*, and the T18 schema anticipates it: the field
is documented as "verbatim from AuditState.remediation_roadmap (CGSA §5.4) **plus
any Phase 6 additions**".
"""
from __future__ import annotations

from typing import Any

#: Materiality → how soon the step is due. A material non-conformity blocks
#: deployment, so it cannot sit in the same bucket as an observation.
PRIORITY_BY_MATERIALITY: dict[str, str] = {
    "material": "immediate",
    "possibly_material": "short_term",
    "observation": "medium_term",
}

#: Working weeks allowed per priority band.
WEEKS_BY_PRIORITY: dict[str, int] = {
    "immediate": 4, "short_term": 12, "medium_term": 26, "long_term": 52,
}

_UNASSIGNED = "[To be assigned]"


def _covered(item: dict[str, Any]) -> set[str]:
    """Identifiers an existing roadmap item already answers for."""
    return {str(item.get(key)) for key in ("finding_id", "control_id") if item.get(key)}


def remediation_roadmap(existing: list[dict[str, Any]],
                        findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge the partner roadmap with a step per uncovered audit finding.

    The partner's own items come first and are never rewritten — they are the
    governance assessment's own product. Audit findings are appended only when
    nothing in the partner roadmap already names them.

    :param existing: ``AuditState.remediation_roadmap`` from CGSA.
    :param findings: Blocking findings raised by the audit.
    :returns: The merged roadmap.
    """
    roadmap = [dict(item) for item in existing or [] if item]
    answered: set[str] = set()
    for item in roadmap:
        answered |= _covered(item)

    for finding in findings or []:
        fid = str(finding.get("finding_id") or "")
        if not fid or fid in answered:
            continue
        priority = PRIORITY_BY_MATERIALITY.get(str(finding.get("materiality")), "medium_term")
        roadmap.append({
            "finding_id": fid,
            "action": (finding.get("recommendation")
                       or f"Remediate {fid} and re-submit the affected evidence."),
            "articles": list(finding.get("eu_ai_act_articles") or []),
            "priority_label": priority,
            "deadline_weeks": WEEKS_BY_PRIORITY[priority],
            "assigned_owner": str(finding.get("assigned_owner") or _UNASSIGNED),
            "source": "audit_finding",
        })
        answered.add(fid)
    return roadmap


__all__ = ["PRIORITY_BY_MATERIALITY", "WEEKS_BY_PRIORITY", "remediation_roadmap"]
