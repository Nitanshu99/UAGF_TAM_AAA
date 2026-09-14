"""Rewriting — never appending to — this phase's own record of what was not admitted.

That is what makes a re-dispatch idempotent, and what lets an artefact admitted
the second time round release the articles it held the first time (Q8).
"""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.unadmitted.records import (
    _entry,
    _is_phase_entry,
    clear_phase_finding,
)
from aaa.agents.tier1.phases.verification.unadmitted.release import _release
from aaa.platform.state.admission import admitted_artefacts
from aaa.tools.regulatory_coverage.engagement_scope import keep_in_scope


def rewrite_phase_records(state: dict, tid_articles: dict[str, list[str]], *,
                          phase_id: str, phase_label: str
                          ) -> tuple[list[str] | None, list[str]]:
    """Replace this phase's unadmitted records and return what they now hold.

    :param state: The mutable AuditState dict.
    :param tid_articles: Template ids this phase emitted, mapped to their articles.
    :param phase_id: Dispatch phase id (``P2``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :returns: ``(unadmitted template ids, in-scope articles they hold)``, or
        ``(None, [])`` when this phase has nothing to record and nothing to clear.
    """
    mine = set(tid_articles)

    def _is_mine(entry: dict) -> bool:
        return _is_phase_entry(entry, phase_id, mine)

    admitted = admitted_artefacts(state)
    unadmitted = [tid for tid in tid_articles if tid not in admitted]
    # Fix 35: a phase that delivered on a later attempt must also clear the
    # no-report record the lost attempt left, not only its unadmitted one.
    clear_phase_finding(state, f"{phase_id or 'P?'}-VERIFY-NOREPORT")
    recorded_before = state.get("unadmitted_artefacts") or []
    previous = [e for e in recorded_before if _is_mine(e)]
    if not unadmitted and not previous:
        return None, []
    entries = [e for e in recorded_before if not _is_mine(e)]
    entries += [_entry(state, tid, tid_articles[tid],
                       phase_id=phase_id, phase_label=phase_label)
                for tid in unadmitted]
    state["unadmitted_artefacts"] = entries
    # Fix 40 (R8): the artefact's contract may claim an article the engagement
    # does not carry. The gate is right; its input was written for a high-risk
    # world. Filtering here keeps `insufficient_evidence_articles` from
    # contradicting the matrix, which is filtered by the same authority.
    articles = keep_in_scope(
        state,
        sorted({a for e in entries if _is_mine(e) for a in e.get("articles") or []}),
        claimed_by=phase_label)
    superseded = {a for e in previous for a in e.get("articles") or []}
    _release(state, superseded - set(articles), entries)
    return unadmitted, articles


__all__ = ["rewrite_phase_records"]
