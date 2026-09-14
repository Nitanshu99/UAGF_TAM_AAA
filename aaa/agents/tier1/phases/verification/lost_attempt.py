"""A dispatch that produced no report: recorded, and its articles held back.

Fix 35: this used to be the last thing that happened — before ``_verify_artefacts``
and before ``gate_on_unadmitted`` — and the runner then wrote a stub in the phase's
place. The articles went unassessed with nothing saying so (R2), and
``phase_has_run`` answered yes to a phase that had produced nothing (R3).
"""
from __future__ import annotations

import logging
import time

from aaa.agents.tier1.phases.verification.no_report import gate_on_no_report
from aaa.agents.tier1.phases.verification.phase_outcome import record_phase_outcome

logger = logging.getLogger(__name__)


def record_lost_attempt(state: dict, tid_articles: dict[str, list[str]],
                        t_agent: float, *, phase_id: str, phase_label: str,
                        rerun_count: int) -> None:
    """Record a phase attempt that returned no report at all.

    F3: without the outcome record the Orchestrator's next envelope still shows
    the *previous* phase's report, so a phase that produced nothing is
    indistinguishable from one that succeeded.

    :param state: The mutable AuditState dict.
    :param tid_articles: Template ids this phase was contracted to emit, mapped
        to the articles each one would have evidenced.
    :param t_agent: ``time.monotonic()`` when the attempt started.
    :param phase_id: Dispatch phase id (``P1``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :param rerun_count: Reruns consumed before this attempt.
    """
    logger.warning("%s: agent produced no report after %.1fs.",
                   phase_label, time.monotonic() - t_agent)
    record_phase_outcome(state, None, list(tid_articles), phase_id=phase_id,
                         phase_label=phase_label, worst=None,
                         rerun_count=rerun_count)
    gate_on_no_report(state, tid_articles,
                      phase_id=phase_id, phase_label=phase_label)


__all__ = ["record_lost_attempt"]
