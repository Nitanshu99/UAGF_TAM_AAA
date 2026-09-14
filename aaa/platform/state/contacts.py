"""Who owns remediation: the Stage A ``organisation_contacts`` roles.

The roles are the T01a contract's; the labels are how a person reads them. One
module, so the wizard asks for the same roles the Phase 5 roadmap assigns to, and
an unassigned item names the role that should take it rather than "To be assigned".
"""
from __future__ import annotations

from typing import Any

#: T01a ``organisation_contacts`` field → the role, as written for a reader.
CONTACT_ROLES: dict[str, str] = {
    "technical_lead": "technical lead",
    "data_lead": "data governance lead",
    "compliance_lead": "compliance / legal lead",
    "dpo": "data protection officer",
    "executive_sponsor": "executive accountable for AI governance",
}


def declared_contacts(raw: Any) -> dict[str, str]:
    """The named contacts, blank and unknown roles dropped.

    :param raw: The declared ``organisation_contacts`` object, or anything else.
    """
    if not isinstance(raw, dict):
        return {}
    return {role: str(raw[role]).strip() for role in CONTACT_ROLES
            if isinstance(raw.get(role), str) and raw[role].strip()}


def owner_for(role: str, contacts: dict[str, Any]) -> str:
    """The declared contact for *role*, or an unassigned owner that names the role.

    :param role: A :data:`CONTACT_ROLES` key.
    :param contacts: Declared contacts.
    """
    named = declared_contacts(contacts).get(role)
    return named or f"To be assigned ({CONTACT_ROLES.get(role, role.replace('_', ' '))})"


__all__ = ["CONTACT_ROLES", "declared_contacts", "owner_for"]
