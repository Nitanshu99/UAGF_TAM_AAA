"""Finding F5 — a phase's own confidence must survive the read, and must matter.

Two defects, one signal.

**It did not survive the read.** ``run_phase_with_verification`` resolved the
value as ``float(report.get("confidence", default) or default)``, and ``0.0 or
0.9`` is ``0.9``: an agent reporting *zero* confidence was recorded as *high*
confidence — the exact inversion of the signal.  The assessed run hit this at
call #009, where the DataAuditor's re-planning reply became the Phase 2 artefact
and reported ``confidence: 0.0``.

**It did not matter.** Even read correctly the number went nowhere: its only
consumer was a note string in ``merge_critique``.  A phase could close saying it
was not confident and still contribute a nominally complete artefact, which the
compliance matrix would then read as evidence and report ``PASS``.

This module is both halves: :func:`read_confidence` reads the number the agent
actually sent, and :func:`gate_on_confidence` gives it a consequence — the
articles of a phase that closes below the floor are recorded
``INSUFFICIENT_EVIDENCE``, the verdict that already means *we could not obtain
sufficient appropriate evidence*.  Since fix 6 that flows on: an unevidenced core
high-risk article derives ``DISCLAIMER_OF_OPINION`` and routes to human review.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.phases.verification.logger import _REPORT_TIDS
from aaa.tools.regulatory_coverage.engagement_scope import keep_in_scope

logger = logging.getLogger(__name__)

#: Below this, a phase's self-reported confidence is treated as an
#: evidence-sufficiency failure rather than a caveat.  0.6 is the band this
#: system already uses for confidence: a CGSA control scoring below it becomes a
#: ``cgsa_low_confidence_controls`` entry, a T14 limitations bullet and a HITL
#: flag (PROMPT.md §Agent 8, ARCHITECTURE.md §CGSA field mapping).  One meaning
#: for one number, rather than a second threshold invented here.
CONFIDENCE_FLOOR: float = 0.6


def read_confidence(report: Any, default: float, phase_label: str = "") -> float:
    """Return the confidence *report* states, falling back only when it states none.

    :param report: The phase agent's Report (or anything else, defensively).
    :param default: The phase's ``default_confidence``, used only when the agent
        reported no value at all.
    :param phase_label: Human-readable phase label used in the logs.
    :returns: The reported confidence, clamped to ``[0.0, 1.0]``.
    """
    raw = report.get("confidence") if isinstance(report, dict) else None
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning("%s: non-numeric confidence %r; using default %.2f.",
                       phase_label, raw, default)
        return default
    if not 0.0 <= value <= 1.0:
        logger.warning("%s: confidence %r out of range; clamped.", phase_label, value)
        return min(max(value, 0.0), 1.0)
    return value


def gate_on_confidence(state: dict, tid_articles: dict[str, list[str]],
                       confidence: float, *, phase_id: str, phase_label: str,
                       floor: float = CONFIDENCE_FLOOR) -> list[str]:
    """Record the articles of a low-confidence phase as unevidenced.

    Report templates (T17/T18) are excluded: they summarise a state that has
    already been assessed, so their confidence says something about the write-up
    rather than about the evidence — the same reasoning ``_critique_artefact``
    applies when it declines to escalate on them.

    :param state: The mutable AuditState dict.
    :param tid_articles: Template ids this phase was contracted to emit, mapped
        to the articles each one evidences.
    :param confidence: The confidence the phase closed with.
    :param phase_id: Dispatch phase id (``P2``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :param floor: Confidence below which the phase's articles are unevidenced.
    :returns: The articles newly marked insufficient by this call.
    """
    if confidence >= floor:
        return []
    # Fix 40 (R8): a low-confidence phase holds back the articles it was
    # accountable for — not the ones its tier-agnostic contract also names.
    articles = keep_in_scope(
        state,
        sorted({article for tid, arts in tid_articles.items()
                if tid not in _REPORT_TIDS for article in arts}),
        claimed_by=phase_label)
    state.setdefault("low_confidence_phases", []).append(
        {"phase_id": phase_id, "phase_label": phase_label,
         "confidence": confidence, "floor": floor, "articles": articles})
    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    newly = [a for a in articles if a not in recorded]
    recorded.extend(newly)
    logger.warning(
        "%s: closed at confidence %.2f, below the %.2f floor — %d article(s) "
        "recorded INSUFFICIENT_EVIDENCE rather than assessed: %s",
        phase_label, confidence, floor, len(newly), ", ".join(newly) or "none new")
    return newly


__all__ = ["CONFIDENCE_FLOOR", "read_confidence", "gate_on_confidence"]
