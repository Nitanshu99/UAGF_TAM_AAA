"""Finding F3 — record what a phase produced, for the Orchestrator's next turn.

``build_envelope`` has always declared ``latest_report`` and ``latest_critique``,
and PROMPT.md §Agent 1 has always instructed the Orchestrator to receive the phase
Report and act on ``critique.verdict``.  Neither was ever produced: every phase
runner discards the ``report`` that ``run_phase_with_verification`` returns and
hands the ReAct loop bare state, and ``verifier_critiques`` is keyed by template
id with no record of which phase wrote which entry or when.  So the Orchestrator
was told an exception had been raised and denied the exception.

This module writes the two compact views onto the state that *does* reach the
loop.  Both are deliberately small — the envelope is re-sent on every turn, so an
artefact is never carried whole, only the fields a sequencing decision turns on.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.phase_outcome.artefact_uri import _resolved_artefact_uri
from aaa.agents.tier1.phases.verification.phase_outcome.fallback import _record_fallback_phase
from aaa.agents.tier1.phases.verification.phase_outcome.views import (
    _SUMMARY_CHARS,
    _blocking_issues,
    _trim,
)


def record_phase_outcome(state: dict, report: Any, tids: list[str], *,
                         phase_id: str, phase_label: str,
                         worst: str | None, rerun_count: int) -> None:
    """Write the ``latest_report`` / ``latest_critique`` envelope views onto *state*.

    :param state: The mutable AuditState, holding ``verifier_critiques``.
    :param report: The phase agent's Report, or ``None`` if it produced none.
    :param tids: Template ids this phase was contracted to emit.
    :param phase_id: Dispatch phase id (``P2``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :param worst: Worst Verifier verdict across *tids*, or ``None`` when the
        agent failed before any artefact could be critiqued.
    :param rerun_count: Reruns consumed reaching this outcome.
    """
    rep = report if isinstance(report, dict) else {}
    _record_fallback_phase(state, rep, tids, phase_id, phase_label)
    state["latest_report"] = {
        "phase_id": phase_id,
        "phase_label": phase_label,
        "produced": bool(rep),
        "summary": _trim(rep.get("summary"), _SUMMARY_CHARS),
        "confidence": rep.get("confidence"),
        "artefact_uri": _resolved_artefact_uri(state, rep, tids, phase_label),
        "template_ids": list(tids),
    }
    if worst is None:
        state["latest_critique"] = None
        return
    critiques = state.get("verifier_critiques") or {}
    state["latest_critique"] = {
        "phase_id": phase_id,
        "phase_label": phase_label,
        "worst_verdict": worst,
        "reruns_used": rerun_count,
        "artefacts": [{
            "template_id": tid,
            "verdict": (critiques.get(tid) or {}).get("verdict"),
            "total_score": (critiques.get(tid) or {}).get("total_score"),
            "blocking_issues": _blocking_issues(critiques.get(tid) or {}),
        } for tid in tids],
    }


__all__ = ["_blocking_issues", "_trim", "record_phase_outcome"]
