"""What each phase owes, and whether it has delivered it.

A phase the model never dispatched leaves its articles unevidenced, and the
compliance matrix then reports them PASS rather than INSUFFICIENT_EVIDENCE —
overstating conformity. The fixed DAG could not skip a phase, so this only
becomes reachable under LLM-decided sequencing.

The "has it run" question is asked from three places — the close-out gate
(:func:`pending_mandatory`), the wrap-up rescue and the Orchestrator's own
observation — so it is answered once, here, rather than re-derived by each.
"""
from __future__ import annotations

from typing import Any

#: artefact each phase must have produced for its articles to be evidenced.
PHASE_ARTEFACT: dict[str, str] = {
    "P1": "T02_system_card", "P2": "T06_datasheet_for_datasets",
    "P3": "T09_model_card", "P4": "T12_output_fairness_report",
    "P5": "T14_governance_findings", "L": "T16_uagf_tam_l_evidence",
}

#: The CSP plan names the privacy branch ``PRIV``; the runner is ``PRIVACY``.
RUNNER_KEY: dict[str, str] = {"PRIV": "PRIVACY"}

#: Plan phases in pipeline order — scope first (P3/P4 size their tests off P1's
#: confirmed modality), the L-branch before the phases it replaces, the tier-3
#: spawns last. P6 is the close-out and is reached by FINALIZE, not sequencing.
PIPELINE_ORDER: tuple[str, ...] = ("P1", "L", "P2", "P3", "P4", "P5", "CYBER", "PRIV")


def phase_has_run(phase: str, state: dict[str, Any],
                  history: list[dict[str, Any]]) -> bool:
    """Has *phase* produced its evidence?

    :param phase: CSP plan phase key.
    :type phase: str
    :param state: The AuditState dict.
    :type state: dict[str, Any]
    :param history: Append-only decision/outcome log.
    :type history: list[dict[str, Any]]
    :returns: ``True`` when the phase's artefact exists, or — for the tier-3
        spawns, which have no artefact contract — when it was ever dispatched.
    :rtype: bool
    """
    artefact = PHASE_ARTEFACT.get(phase)
    if artefact:
        return artefact in (state.get("phase_artefacts") or {})
    key = RUNNER_KEY.get(phase, phase)
    return any(h.get("action") == "DISPATCH" and h.get("phase_id") == key
               for h in history)


def phase_progress(state: dict[str, Any],
                   history: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Report which phases have run and which mandatory ones are still owed.

    Finding F4: the envelope listed admitted *template ids* and nothing else, so
    the model inferred phase state from an id prefix — read the intake artefacts
    ``T01a``/``T01b``/``T01c`` as "Phase 1 complete" and dispatched P2 while P1
    had never run. Phase state is now stated rather than inferred.

    :param state: The AuditState dict.
    :type state: dict[str, Any]
    :param history: Append-only decision/outcome log.
    :type history: list[dict[str, Any]]
    :returns: ``{"completed": [...], "outstanding": [...]}`` in pipeline order;
        ``outstanding`` holds only phases the plan marks mandatory.
    :rtype: dict[str, list[str]]
    """
    plan = state.get("phase_plan") or {}
    completed = [p for p in PIPELINE_ORDER if phase_has_run(p, state, history)]
    outstanding = [p for p in PIPELINE_ORDER
                   if str(plan.get(p, "")).upper() == "M" and p not in completed]
    return {"completed": completed, "outstanding": outstanding}


def pending_mandatory(state: dict[str, Any], dispatched: dict[str, int],
                      cap: int) -> str | None:
    """Return the first mandatory phase that has not produced its artefact.

    Only phases the CSP plan explicitly marks ``M`` are required, so an
    empty plan (the planner has not run yet) never blocks. Phases already
    dispatched to *cap* are skipped so a failing phase cannot deadlock.

    :param state: The mutable AuditState dict.
    :type state: dict[str, Any]
    :param dispatched: Dispatch counts per phase id so far.
    :type dispatched: dict[str, int]
    :param cap: Maximum dispatches allowed per phase.
    :type cap: int
    :returns: Phase id still owed, or ``None`` when all are satisfied.
    :rtype: str | None
    """
    plan = state.get("phase_plan") or {}
    produced = set((state.get("phase_artefacts") or {}).keys())
    for phase, artefact in PHASE_ARTEFACT.items():
        if (str(plan.get(phase, "")).upper() == "M" and artefact not in produced
                and dispatched.get(phase, 0) < cap):
            return phase
    return None
