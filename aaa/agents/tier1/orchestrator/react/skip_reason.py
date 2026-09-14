"""Why a mandatory phase must not be forced in the wrap-up, or None to run it."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.coverage import RUNNER_KEY, phase_has_run
from aaa.agents.tier1.orchestrator.react.guards import _PHASE_CAP, INTAKE_GATE
from aaa.agents.tier1.orchestrator.react.runners_map import RUNNERS

_DONE = "done"
def _skip_reason(phase: str, state: dict[str, Any],
                 history: list[dict[str, Any]]) -> str | None:
    """Why *phase* must not be forced now, or ``None`` to run it.

    :param phase: CSP plan phase key.
    :param state: The AuditState dict.
    :param history: Append-only decision/outcome log.
    :returns: ``_DONE``, a human-readable reason, or ``None``.
    """
    if str((state.get("phase_plan") or {}).get(phase, "")).upper() != "M":
        return _DONE  # optional or skipped: not owed, and not a coverage gap
    if phase_has_run(phase, state, history):
        return _DONE
    key = RUNNER_KEY.get(phase, phase)
    if key not in RUNNERS:
        return f"no runner registered for {phase}"
    score = state.get("intake_completeness_score")
    if phase == "P1" and score is not None and float(score) < INTAKE_GATE:
        return f"intake_completeness_score {score} < {INTAKE_GATE} blocks Phase 1"
    dispatched = sum(1 for h in history
                     if h.get("action") == "DISPATCH" and h.get("phase_id") == key)
    if dispatched >= _PHASE_CAP:
        return f"already dispatched {dispatched} time(s), at the cap"
    return None


__all__ = ["_DONE", "_skip_reason"]
