"""Stamping a deliverable with what the run actually was before it is written.

F2 (S3): stamped *before* the write, so every consumer of the deliverable can tell a
placeholder run from a real one without inferring it from whichever downstream field
happened to come back empty. F16 (S24): the S6 field projection is stamped here too —
it had been correct since F8-F15 but nothing wrote it into the file a human opens.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.data.writer.schema_stamp import stamp_schema_violations
from aaa.integrations.s6_contract import S6_CONTRACT_WARNINGS_KEY, S6_FIELDS_KEY, build_s6_fields
from aaa.platform.state.run_integrity import RUN_INTEGRITY_KEY, build_run_integrity

logger = logging.getLogger(__name__)


def stamp_integrity(final_state: dict[str, Any], engagement_id: str, store: Any) -> None:
    """Record run integrity and the S6 projection on *final_state*, in place.

    :param final_state: The finished AuditState, mutated.
    :param engagement_id: Engagement identifier, for the log lines.
    :param store: The evidence store the URIs point into.
    """
    # P9: these files address every artefact by minio:// URI. On a
    # process-local backend they are already dangling as they are written,
    # and only the store knows that — the URIs themselves look identical.
    if not getattr(store, "is_durable", False):
        logger.error(
            "Customer export: the evidence backend does not persist beyond "
            "this process, so every minio:// URI in %s's audit_state / T17 / "
            "T18 is unresolvable from the moment it is written. Set "
            "EVIDENCE_BACKEND=minio and re-run for a traceable evidence chain.",
            engagement_id)
    # F2 (S3): stamp before the write, so every consumer of the deliverable
    # can tell a placeholder run from a real one without inferring it from
    # whichever downstream field happened to come back empty.
    integrity = build_run_integrity(final_state)
    stamp_schema_violations(integrity, final_state, engagement_id, store)
    final_state[RUN_INTEGRITY_KEY] = integrity
    if not integrity["suitable_for_handoff"]:
        logger.error(
            "Customer export: %s is a DEGRADED run — %d of %d artefacts are "
            "placeholders, %d were admitted on a critique the Verifier's model "
            "never wrote (%s), and phase(s) %s delivered nothing. The audit "
            "state is written for inspection but must not be handed to a "
            "downstream consumer. Unwired agents: %s.",
            engagement_id, len(integrity["stub_artefact_ids"]),
            integrity["artefact_count"], len(integrity["fallback_critique_ids"]),
            ", ".join(integrity["fallback_critique_ids"]) or "none",
            ", ".join(integrity["degraded_phases"]) or "none",
            ", ".join(integrity["unwired_agents"]) or "none recorded")
    # F16 (S24): stamp the S6 field projection into the deliverable itself.
    # build_s6_fields has been correct since F8-F15, but until now it was
    # only ever passed to build_handoff for the mid-pipeline external XAI /
    # security evaluate-API call — nothing wrote it into the file a human
    # (or S6's own tooling) opens under data/customer/. A reviewer reading
    # the raw audit_state.json saw none of that derivation.
    s6_fields, s6_warnings = build_s6_fields(final_state)
    final_state[S6_FIELDS_KEY] = s6_fields
    final_state[S6_CONTRACT_WARNINGS_KEY] = s6_warnings
    if s6_warnings:
        logger.warning("Customer export: %s s6_fields carries %d contract "
                       "warning(s): %s", engagement_id, len(s6_warnings), s6_warnings)


__all__ = ["stamp_integrity"]
