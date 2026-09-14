"""Finding F4 — a phase must not run before the phase it depends on.

At turn 1 the assessed run dispatched **P2 before P1**. The model's rationale
names its evidence: *"Phase 1 artefacts admitted"* — it had read the intake
artefacts ``T01a``/``T01b``/``T01c`` as Phase 1 output. Phase 1's real contract
is ``T02_system_card``, which did not exist. Nothing caught it: ``apply_guards``
reasoned about the Art. 5 halt, the intake gate, the dispatch cap and close-out
ordering, and ``pending_mandatory`` — the only function that reasons about
outstanding phases — ran solely at close-out. The run logged zero overrides.

DataAuditor therefore ran without P1's *confirmed* risk tier, modality or
Annex III mapping, and without ``T02_system_card`` in its evidence chain; its
Dispatch carried the client's own declared values instead. For Phase 2 that is
survivable. For P3/P4, which size robustness and fairness testing off the
confirmed modality, it silently mis-scopes the tests.

The map is deliberately thin: only dependencies the code itself asserts.
Everything downstream of scope needs P1's confirmed classification; P4 follows
P3 because Phase 3 owns the load-level findings Phase 4 suppresses to avoid
duplicating (``output_fairness/inputs.py``: *"Load-level findings are owned by
Phase 3 — only the scored result is consumed here"*). A prerequisite that the
plan does not mark mandatory is not a prerequisite at all — under the L-branch,
P3 is skipped and P4's dependency on it simply does not arise.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import phase_has_run

#: Phases that must have delivered before a phase may be dispatched, in the
#: order they should be run. Keys and values are dispatchable phase ids.
PHASE_PREREQS: dict[str, tuple[str, ...]] = {
    "P2": ("P1",),
    "P3": ("P1",),
    "P4": ("P1", "P3"),
    "P5": ("P1",),
    "L": ("P1",),
    "CYBER": ("P1",),
    "PRIVACY": ("P1",),
}


def missing_prerequisite(phase_id: str, state: dict[str, Any],
                         history: list[dict[str, Any]],
                         dispatched: dict[str, int], cap: int) -> str | None:
    """Return the prerequisite *phase_id* is missing, or ``None`` to allow it.

    A prerequisite is enforced only when it is genuinely owed and genuinely
    runnable: one the plan does not mark mandatory is not required, and one
    already at its dispatch cap has been tried and failed — blocking on it
    would deadlock the audit rather than order it.

    :param phase_id: The phase the model proposes to dispatch.
    :type phase_id: str
    :param state: The AuditState dict.
    :type state: dict[str, Any]
    :param history: Append-only decision/outcome log.
    :type history: list[dict[str, Any]]
    :param dispatched: Dispatch counts per phase id so far.
    :type dispatched: dict[str, int]
    :param cap: Maximum dispatches allowed per phase.
    :type cap: int
    :returns: The first prerequisite that must run first, else ``None``.
    :rtype: str | None
    """
    plan = state.get("phase_plan") or {}
    for prereq in PHASE_PREREQS.get(phase_id, ()):
        if str(plan.get(prereq, "")).upper() != "M":
            continue
        if phase_has_run(prereq, state, history):
            continue
        if dispatched.get(prereq, 0) >= cap:
            continue
        return prereq
    return None


__all__ = ["PHASE_PREREQS", "missing_prerequisite"]
