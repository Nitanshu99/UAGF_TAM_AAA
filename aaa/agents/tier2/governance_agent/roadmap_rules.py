"""The rules that turn a CGSA roadmap row into an owned, dated remediation item.

Three defects lived here (T-20260913-008). The severity map knew only the legacy
``critical/major/minor/observation`` dialect, while the CGSA schema and T14 use
``critical/high/medium/low`` — so every ``high`` and ``medium`` gap fell through to
``long_term`` and 52 weeks, where the source said 4 and 2. ``domain_id`` was read
from the roadmap row, which never carries one, so every owner defaulted to the
technical lead. And the source's own ``timeline_weeks`` was ignored.
"""
from __future__ import annotations

from typing import Any

#: CGSA domain → the ``organisation_contacts`` role that owns its remediation. D6
#: (Monitoring and Incident Response) went to the DPO, whose remit is personal-data
#: breaches, not operating AI monitoring; D1 (Risk Management — the Art. 9 system)
#: went to the technical lead rather than the executive accountable for AI
#: governance, which is how the T01a contract describes ``executive_sponsor``.
DOMAIN_TO_OWNER_FIELD = {
    "D1": "executive_sponsor", "D2": "data_lead", "D3": "technical_lead",
    "D4": "compliance_lead", "D5": "compliance_lead", "D6": "technical_lead",
}

#: ``(priority_label, fallback deadline in weeks)``, for both dialects.
SEVERITY_MAP = {
    "critical": ("immediate", 4),
    "high": ("short_term", 12), "major": ("short_term", 12),
    "medium": ("medium_term", 26), "minor": ("medium_term", 26),
    "low": ("long_term", 52), "observation": ("long_term", 52),
}


def control_domains(payload: Any) -> dict[str, str]:
    """``{control_id: domain_id}`` from the CGSA ``domains`` tree.

    :param payload: Raw CGSA payload.
    :returns: The domain each control belongs to; empty when there is no tree.
    """
    if not isinstance(payload, dict):
        return {}
    return {str(ctrl.get("control_id")): str(dom.get("domain_id") or "")
            for dom in payload.get("domains") or [] if isinstance(dom, dict)
            for ctrl in dom.get("controls") or [] if isinstance(ctrl, dict)}


def deadline_weeks(item: dict[str, Any], source: dict[str, Any], fallback: int) -> int:
    """The source's own ``timeline_weeks`` when it gave one, else the severity default.

    :param item: The ingested roadmap item.
    :param source: The raw CGSA row at the same position.
    :param fallback: The severity-derived deadline.
    :returns: Weeks until the gap should be closed.
    """
    for candidate in (item.get("timeline_weeks"), source.get("timeline_weeks")):
        if isinstance(candidate, int) and not isinstance(candidate, bool) and candidate > 0:
            return candidate
    return fallback


__all__ = ["DOMAIN_TO_OWNER_FIELD", "SEVERITY_MAP", "control_domains", "deadline_weeks"]
