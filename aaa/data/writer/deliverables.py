"""The T17 and T18 payloads written into the customer folder, and the HITL packet."""
from __future__ import annotations

import logging
import pathlib
from typing import Any

from aaa.data.writer.atomic import _write

logger = logging.getLogger(__name__)


def write_deliverables(cdir: pathlib.Path, engagement_id: str, artefacts: dict,
               final_state: dict, store: Any) -> dict[str, Any]:
    """Write T17, T18 and — when the run deferred cases — the HITL review packet.

    :param cdir: The customer folder.
    :param engagement_id: Engagement identifier.
    :param artefacts: ``phase_artefacts`` from the final state.
    :param final_state: The finished AuditState.
    :param store: The evidence store the artefact URIs resolve against.
    :returns: The payloads that were found, keyed ``T17`` / ``T18``.
    """
    deliverables: dict[str, Any] = {}
    deliverables: dict[str, Any] = {}
    for tid, suffix in (("T17_compliance_matrix", "T17"), ("T18_audit_report", "T18")):
        ref = artefacts.get(tid)
        uri = ref.get("uri") if isinstance(ref, dict) else None
        payload = store.get_artefact(uri) if uri else None
        if payload is not None:
            deliverables[suffix] = payload
            _write(cdir / f"{engagement_id}_{suffix}.json", payload)
        else:
            logger.warning("Customer export: %s payload unavailable for %s",
                           tid, engagement_id)

    # Deferred HITL cases → emit an editable review packet for the human auditor.
    from aaa.tools.hitl_review import build_hitl_review_packet, hitl_cases
    if hitl_cases(final_state) or final_state.get("hitl_required"):
        packet = build_hitl_review_packet(final_state)
        _write(cdir / f"{engagement_id}_hitl_review.json", packet)
        logger.info("Saved HITL review packet: %s (%d case(s)) → %s",
                    engagement_id, len(packet.get("cases", [])), cdir)

    return deliverables


__all__ = ["write_deliverables"]
