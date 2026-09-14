"""Guarded extraction of partner (S6/S7) sections from their response.

Contract: the external S6/S7 API echoes the FULL audit-state JSON back with
only its own section populated. S5 never trusts the echo beyond that section:
:func:`extract_partner_sections` returns *only* the named section's content,
discarding everything else — the caller never even sees, let alone applies,
any other field the echo carries. A protected field present in the echo is
logged as a clobber attempt regardless of its value, since a well-behaved
partner should never need to touch it either way.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Fields a well-behaved partner should never need to echo back changed.
_PROTECTED_FIELDS = (
    "final_verdict", "blocking_findings", "positive_findings",
    "compliance_matrix", "phase_artefacts", "auditor_opinion",
    "cgsa_governance_verdict", "cgsa_phase5_verdict",
)


def extract_partner_sections(response: Any, section_key: str, label: str) -> dict[str, Any]:
    """Extract *section_key*'s content from a partner response, discarding the rest.

    Accepts either a full audit-state echo (``{"audit_state": {...}}`` or the
    state directly at the top level — detected via the ``client_submission``
    sentinel key, which only ever exists on a real ``AuditState``) or a bare
    section response (the section's content directly, no wrapper — kept for
    partner APIs still in flux).

    :param response: The parsed HTTP response body.
    :type response: Any
    :param section_key: The single state key this provider owns
        (``"xai_evidence"`` or ``"security_evidence"``).
    :type section_key: str
    :param label: Log label (``xai`` / ``security``).
    :type label: str
    :returns: The section's content, or ``{}`` when absent/malformed.
    :rtype: dict[str, Any]
    """
    if not isinstance(response, dict):
        return {}
    source = response.get("audit_state")
    source = source if isinstance(source, dict) else response

    if "client_submission" not in source:
        return source  # Bare-section response — nothing to guard against.

    clobbered = [f for f in _PROTECTED_FIELDS if f in source]
    if clobbered:
        logger.warning("%s echo touched protected state field(s) %s — discarded, not applied.",
                       label, clobbered)
    section = source.get(section_key)
    return section if isinstance(section, dict) else {}
