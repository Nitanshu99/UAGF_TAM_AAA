"""Closing a phase: the two evidence gates, and the outcome the Orchestrator reads next."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.confidence import gate_on_confidence
from aaa.agents.tier1.phases.verification.finish_phase import _finish_phase
from aaa.agents.tier1.phases.verification.phase_outcome import record_phase_outcome
from aaa.agents.tier1.phases.verification.provider_findings import record_provider_findings
from aaa.agents.tier1.phases.verification.unadmitted import gate_on_unadmitted


def close_phase(state: dict, report: Any, tid_articles: dict[str, list[str]],
                confidence: float, worst: str, *, rerun_count: int,
                t_phase: float, phase_id: str, phase_label: str, load: Any = None) -> None:
    """Run the closing gates and record the phase outcome.

    F5: an artefact its own author does not stand behind is not evidence —
    below the floor the phase's articles are recorded INSUFFICIENT_EVIDENCE
    instead of contributing a nominally complete artefact to the matrix.
    P6 + Q1: the admission gate is read after the rerun loop, from the critiques
    as they finally stand, so an artefact rejected on attempt 1 and admitted on
    attempt 2 leaves no stale insufficiency behind. F3: the phase runners discard
    *report*, so this is the only place the Report and its critiques are both in
    hand — they are recorded for the Orchestrator's next observation.

    :param state: The mutable AuditState dict.
    :param report: The phase agent's Report.
    :param tid_articles: Template ids emitted, mapped to the articles each evidences.
    :param confidence: The confidence the agent reported.
    :param worst: Worst Verifier verdict across the artefacts.
    :param rerun_count: Reruns consumed reaching this outcome.
    :param t_phase: ``time.monotonic()`` when the phase started.
    :param phase_id: Dispatch phase id (``P2``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :param load: Reads a stored artefact by URI (the agent's evidence store), if available.
    """
    _finish_phase(state, worst, rerun_count, phase_label, t_phase)
    gate_on_confidence(state, tid_articles, confidence,
                       phase_id=phase_id, phase_label=phase_label)
    gate_on_unadmitted(state, tid_articles,
                       phase_id=phase_id, phase_label=phase_label)
    # Option A: what admitted artefacts record about the provider decides their articles.
    record_provider_findings(state, tid_articles, phase_id=phase_id, phase_label=phase_label,
                             load=load)
    record_phase_outcome(state, report, list(tid_articles), phase_id=phase_id,
                         phase_label=phase_label, worst=worst,
                         rerun_count=rerun_count)


__all__ = ["close_phase"]
