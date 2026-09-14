"""Audit-state summary envelope for the Orchestrator ReAct user message.

Builds the compact JSON observation defined in PROMPT.md §Agent 1 — the
model never receives raw artefacts, only the summary plus the latest report
and critique, keeping every decision call small and cache-friendly.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import phase_progress


def _admitted(state: dict[str, Any]) -> list[str]:
    """Return the template ids of phase artefacts admitted so far.

    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :returns: Sorted template-id list.
    :rtype: list[str]
    """
    return sorted((state.get("phase_artefacts") or {}).keys())


def _admitted_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    """The admitted artefacts *with the verdict each was admitted under* (M14).

    ``phase_artefacts_not_admitted`` has always carried a verdict per entry and
    this list has always been bare template ids, so the planner could quote a
    verdict for a rejected artefact and had to paraphrase for an accepted one.
    It paraphrased into the register the rest of the prompt speaks — uppercase —
    and produced ``ACCEPT_WITH_NOTICES`` (#041) and ``ACCEPT_WITH_NOTES`` (#067),
    neither of which is a verdict this system emits.

    An intake artefact no phase produced carries ``verdict: null``, which is the
    honest answer: it was never critiqued.

    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :returns: One record per admitted artefact, sorted by template id.
    :rtype: list[dict[str, Any]]
    """
    critiques = state.get("verifier_critiques") or {}
    return [{"template_id": tid, "verdict": (critiques.get(tid) or {}).get("verdict")}
            for tid in _admitted(state)]


def turn_outcome(state: dict[str, Any], before: list[str]) -> dict[str, Any]:
    """Summarise what a ReAct turn changed, for the next observation.

    :param state: The mutable AuditState dict after the action.
    :type state: dict[str, Any]
    :param before: Artefact template ids admitted before the action.
    :type before: list[str]
    :returns: Compact outcome summary.
    :rtype: dict[str, Any]
    """
    return {"new_artefacts": [t for t in _admitted(state) if t not in before],
            "hitl_required": bool(state.get("hitl_required")),
            "blocking_findings": len(state.get("blocking_findings") or []),
            "final_verdict": state.get("final_verdict")}


def build_envelope(state: dict[str, Any],
                   history: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the per-turn user payload for the Orchestrator model.

    ``phases_completed`` / ``phases_outstanding`` state what
    ``phase_artefacts_admitted`` could only be guessed from: the assessed run's
    model read the intake artefacts ``T01a``/``T01b``/``T01c`` as "Phase 1
    complete" and dispatched P2 while P1 had never run (finding F4). The
    artefact list is kept — it says what exists — but phase state is no longer
    inferred from an id prefix.

    ``latest_report`` and ``latest_critique`` are read from the state written by
    ``verification.phase_outcome.record_phase_outcome``, and ``hitl_reason``
    from the state written by ``verification.finish_phase``. They were once
    optional parameters that no call site ever supplied (finding F3), which left
    the model observing ``hitl_required: true`` with no report, no critique and
    no reason — so they are deliberately *not* parameters any more: there is one
    source for them and a new call site cannot silently drop them again.

    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :param history: Prior decisions + outcomes this engagement (append-only).
    :type history: list[dict[str, Any]]
    :returns: JSON-serialisable envelope per PROMPT.md §Agent 1.
    :rtype: dict[str, Any]
    """
    cgsa = state.get("cgsa_payload") or {}
    progress = phase_progress(state, history)
    return {
        "engagement_id": state.get("engagement_id"),
        "audit_state_summary": {
            "intake_completeness_score": state.get("intake_completeness_score"),
            "declared_modality": state.get("declared_modality", ""),
            "declared_risk_tier": state.get("declared_risk_tier", ""),
            "declared_annex_iii_sections": state.get("declared_annex_iii_sections", []),
            "is_llm_or_agentic": bool(state.get("is_llm_or_agentic")),
            "risk_tier": state.get("risk_tier"),
            "cgsa_phase5_verdict": cgsa.get("phase5_verdict"),
            "phase_plan": state.get("phase_plan"),
            "phase_artefacts_admitted": _admitted_records(state),
            # Stated, not left to be inferred from absence. Shown only the
            # admitted list, the planner read a short list as a complete one:
            # at call #051 of the 2026-09-09 run it moved to ASSEMBLE_MATRIX
            # reasoning "all mandatory phases have completed with
            # Verifier-admitted artefacts" while five artefacts — T05, T09, T11,
            # T13, T15 — had been escalated rather than admitted. Sequencing on
            # that belief is how an article reaches the matrix believing it was
            # evidenced.
            "phase_artefacts_not_admitted": [
                {"template_id": entry.get("template_id"),
                 "verdict": entry.get("verdict"),
                 "articles_held": entry.get("articles") or []}
                for entry in (state.get("unadmitted_artefacts") or [])],
            "phases_completed": progress["completed"],
            "phases_outstanding": progress["outstanding"],
            "hitl_required": bool(state.get("hitl_required")),
            "hitl_reason": state.get("hitl_reason"),
            "blocking_findings": len(state.get("blocking_findings") or []),
        },
        "decision_history": history,
        "latest_report": state.get("latest_report"),
        "latest_critique": state.get("latest_critique"),
    }
