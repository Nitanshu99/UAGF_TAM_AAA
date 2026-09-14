"""Which CGSA assessment Phase 5 reads, and the record of that choice.

The declared assessment is pulled first. When it is a self-assessment export and
exactly one evaluated export of the same organisation and system is on file, that
export is read instead — the rule the wizard's name lookup already applies — so every
entry point audits against the same assessment (T-20260914-062). The state records
which one was read, so a result can show it came from an evaluated export.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.cgsa_pull import CGSAPullError, cgsa_pull
from aaa.tools.cgsa_pull.compat import is_evaluated
from aaa.tools.cgsa_pull.supersede import evaluated_counterpart

logger = logging.getLogger(__name__)


def cgsa_source(payload: Any, declared: str | None, superseded: bool) -> dict[str, Any]:
    """``{assessment_id, declared_assessment_id, evaluated, superseded}`` for the state."""
    meta = (payload.get("metadata") or {}) if isinstance(payload, dict) else {}
    return {"assessment_id": meta.get("assessment_id"), "declared_assessment_id": declared or None,
            "evaluated": isinstance(payload, dict) and is_evaluated(payload),
            "superseded": superseded}


def pull_assessment(declared: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pull the declared assessment, or the evaluated export that supersedes it.

    :param declared: The dossier's ``cgsa_assessment_id``.
    :returns: ``(payload, cgsa_source)``.
    :raises CGSAPullError: When the declared assessment cannot be pulled.
    """
    payload = cgsa_pull(assessment_id=declared)
    counterpart = evaluated_counterpart(payload)
    if counterpart:
        try:
            payload = cgsa_pull(assessment_id=counterpart)
        except CGSAPullError as exc:
            logger.warning("CGSA: evaluated export %s could not be pulled (%s); reading the "
                           "declared %s.", counterpart, exc.reason, declared)
            return payload, cgsa_source(payload, declared, False)
        logger.info("CGSA: declared %s is a self-assessment export; reading the evaluated "
                    "export %s of the same system.", declared, counterpart)
    return payload, cgsa_source(payload, declared, bool(counterpart))


def source_note(source: dict[str, Any] | None) -> str:
    """The T14 sentence naming a substituted assessment, or ``""``."""
    if not source or not source.get("superseded"):
        return ""
    return (f" The dossier declared CGSA assessment '{source['declared_assessment_id']}', a "
            "self-assessment export whose controls carry no threshold; the evaluated export "
            f"'{source['assessment_id']}' of the same organisation and system supersedes it "
            "and is the assessment read here.")


__all__ = ["cgsa_source", "pull_assessment", "source_note"]
