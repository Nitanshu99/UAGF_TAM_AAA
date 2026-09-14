"""Releasing an article from the insufficiency when nothing holds it back any more."""
from __future__ import annotations

import logging

from aaa.platform.state.admission import ADMITTED_VERDICTS

logger = logging.getLogger(__name__)


def _held_articles(state: dict, entries: list[dict]) -> set[str]:
    """Articles still unevidenced by *entries* or by a low-confidence phase."""
    # A material evidence gap on an admitted artefact holds its articles too (T-20260914-016).
    held = {a for e in [*entries, *(state.get("evidence_gap_records") or [])]
            for a in e.get("articles") or []}
    return held | {a for p in state.get("low_confidence_phases") or []
                   for a in p.get("articles") or []}


def _release(state: dict, candidates: set[str], entries: list[dict]) -> list[str]:
    """Drop *candidates* from the insufficiency unless something still holds them."""
    released = sorted(candidates - _held_articles(state, entries))
    if released:
        state["insufficient_evidence_articles"] = [
            a for a in state.get("insufficient_evidence_articles") or []
            if a not in released]
    return released


def clear_unadmitted_insufficiency(state: dict) -> list[str]:
    """Release articles held insufficient by artefacts a human has since admitted.

    The gate must not be one-way. When a reviewer critiques an artefact the
    Verifier rejected or could not reach and admits it, the reason its articles
    were unevidenced is gone — but only that reason: an article another
    unadmitted artefact still names, or one a low-confidence phase contributed,
    stays.

    :param state: The AuditState, after ``apply_human_decisions``.
    :returns: The articles released, sorted.
    """
    entries = state.get("unadmitted_artefacts") or []
    if not entries:
        return []
    critiques = state.get("verifier_critiques") or {}

    def _admitted(entry: dict) -> bool:
        return (critiques.get(entry.get("template_id"), {})
                .get("verdict") in ADMITTED_VERDICTS)

    still = [e for e in entries if not _admitted(e)]
    candidates = {a for e in entries if _admitted(e) for a in e.get("articles") or []}
    released = _release(state, candidates, still)
    state["unadmitted_artefacts"] = still
    if released:
        logger.info("HITL admitted %d previously unadmitted artefact(s); released %s.",
                    len(entries) - len(still), ", ".join(released))
    return released


__all__ = ["_held_articles", "_release", "clear_unadmitted_insufficiency"]
