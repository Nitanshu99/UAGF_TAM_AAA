"""Narrowing a set of discovered assessments down to the one this engagement means."""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.cgsa_pull.discover import discover_assessments
from aaa.tools.cgsa_pull.tokens import _org_tokens, _system_tokens

logger = logging.getLogger(__name__)


def _narrow(candidates: list[dict[str, Any]], system: str) -> list[dict[str, Any]]:
    """Reduce several assessments for one organisation to a single answer.

    The system name is tried first. What remains is then read for dialect: an
    evaluated export and a self-assessment of the *same* system are not two
    assessments to choose between — the evaluated one supersedes, because only
    it carries the thresholds a control-level non-conformity is derived from.
    Calling that a tie and returning nothing would drop the evidence Phase 5
    exists to read, which is the same outcome as pulling the thin one.

    :param candidates: Assessments whose organisation already matched.
    :param system: System name as the customer gave it.
    :returns: One assessment, or several when they remain genuinely ambiguous.
    """
    named = _system_tokens(system)
    narrowed = [a for a in candidates if named
                and named <= _system_tokens(a["system_under_audit"])]
    if len(narrowed) == 1:
        return narrowed
    pool = narrowed or candidates
    evaluated = [a for a in pool if a.get("evaluated")]
    return evaluated if len(evaluated) == 1 else pool
def resolve_assessment_id(
    organisation: str, system: str = "", roots: list[str] | None = None,
) -> str | None:
    """Find the one assessment filed for this organisation and system.

    :param organisation: Legal provider name as the customer gave it.
    :param system: System name, used only to break a tie.
    :param roots: Directories to search; defaults to :func:`fixture_roots`.
    :returns: The assessment id, or ``None`` if nothing matched or more than
        one did.
    """
    wanted = _org_tokens(organisation)
    if not wanted:
        return None
    candidates = [a for a in discover_assessments(roots)
                  if _org_tokens(a["organisation_name"]) == wanted]
    if len(candidates) > 1:
        candidates = _narrow(candidates, system)
    if len(candidates) != 1:
        logger.info("cgsa discovery: %d assessment(s) match %r / %r; "
                    "proceeding without one.", len(candidates), organisation, system)
        return None
    logger.info("cgsa discovery: %r matched %s", organisation,
                candidates[0]["assessment_id"])
    return candidates[0]["assessment_id"]


__all__ = ["_narrow", "resolve_assessment_id"]
