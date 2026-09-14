"""Finding F12 — a budget-exhausted audit must finish its work, not cancel it.

``deterministic_wrapup`` used to mark the outstanding phases unevidenced, assemble
the matrix and jump to Phase 6. Running out of ReAct turns therefore *silently
cancelled* every phase the model had not reached — six of eight on the assessed
run, on a submission scoring ``intake_completeness_score = 1.0``. The delivered
report said `PASS_WITH_OBSERVATIONS`.

``unevidenced.py`` argued that marking was the right response because dispatching
would be "an unbounded rescue loop". That is a false dichotomy: one attempt per
outstanding mandatory phase is bounded by the phase list itself — at most six
runs — and the existing per-phase dispatch cap bounds it further. Marking is the
right response only for a phase that *cannot* run; this module establishes which
those are by trying.

The gates the ReAct loop enforces per turn are enforced here too, because the
wrap-up path bypasses ``apply_guards`` entirely: an Art. 5 halt stops the rescue
outright, and the intake gate still blocks Phase 1. The order it forces phases in
is ``coverage.PIPELINE_ORDER``, the same order the precedence guard (F4) enforces
during normal sequencing.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import PIPELINE_ORDER, RUNNER_KEY
from aaa.agents.tier1.orchestrator.react.runners_map import RUNNERS
from aaa.agents.tier1.orchestrator.react.skip_reason import _DONE, _skip_reason
from aaa.agents.tier1.orchestrator.react.summary import _admitted, turn_outcome

logger = logging.getLogger(__name__)





async def run_outstanding(agents: dict[str, Any], state: dict[str, Any],
                          history: list[dict[str, Any]]) -> tuple[dict[str, Any], dict]:
    """Run each mandatory phase the loop never reached, once.

    :param agents: Agent registry from ``initialise_agents``.
    :param state: The mutable AuditState dict.
    :param history: Append-only decision/outcome log, extended in place.
    :returns: ``(state, {"forced": [...], "skipped": [...]})``.
    """
    if state.get("risk_tier") == "prohibited":
        logger.warning("Wrap-up: Art. 5 halt in force — no phase may be dispatched.")
        return state, {"forced": [], "skipped": [{"phase": p, "reason": "Art.5 halt"}
                                                 for p in PIPELINE_ORDER]}
    forced: list[str] = []
    skipped: list[dict[str, str]] = []
    for phase in PIPELINE_ORDER:
        reason = _skip_reason(phase, state, history)
        if reason == _DONE:
            continue
        if reason:
            skipped.append({"phase": phase, "reason": reason})
            logger.warning("Wrap-up: mandatory phase %s not run — %s.", phase, reason)
            continue
        key = RUNNER_KEY.get(phase, phase)
        before = _admitted(state)
        logger.warning("Wrap-up: forcing mandatory phase %s, which the turn budget "
                       "did not reach.", key)
        try:
            state = await RUNNERS[key](agents, state)
        # A rescue run must never crash the audit — the whole point of this path
        # is that something already went wrong.
        except Exception as exc:  # noqa: BLE001
            skipped.append({"phase": phase, "reason": f"runner failed: {exc}"})
            logger.error("Wrap-up: phase %s failed (%s); its articles stay "
                         "unevidenced.", key, exc)
            continue
        forced.append(key)
        history.append({"turn": "wrapup", "action": "DISPATCH", "phase_id": key,
                        "rationale": "wrap-up: mandatory phase not reached in budget",
                        "guard_override": "forced by deterministic wrap-up",
                        "outcome": turn_outcome(state, before), "forced": True})
    return state, {"forced": forced, "skipped": skipped}


__all__ = ["run_outstanding"]
