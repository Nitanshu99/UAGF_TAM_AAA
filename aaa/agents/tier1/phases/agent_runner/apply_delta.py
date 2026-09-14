"""Merging a phase's declaration_verification_delta onto the mutable AuditState."""
from __future__ import annotations

from aaa.agents.tier1.phases.agent_runner.dedup_accumulated import _dedup_accumulated
from aaa.agents.tier1.phases.agent_runner.logger import _ACCUMULATE_KEYS
from aaa.platform.state.artefact_keys import namespace_artefacts


def _apply_delta(state: dict, delta: dict, spawn: str | None = None) -> None:
    """Merge a declaration_verification_delta onto the mutable AuditState.

    ``phase_artefacts`` is merged with ``update`` because a phase re-dispatched
    after a ``rerun`` verdict legitimately replaces its own artefact. A tier-3
    spawn does not: it produces a second copy of a template a phase owns, so
    *spawn* re-keys its artefacts into that spawn's namespace before the merge
    and the phase's own entry — and the critique attached to it — survives (P5).

    :param state: The mutable AuditState dict.
    :param delta: The agent's declaration_verification_delta.
    :param spawn: Tier-3 spawn namespace, when the delta comes from one.
    """
    for key, value in delta.items():
        if key == "phase_artefacts":
            artefacts = value or {}
            if spawn:
                artefacts = namespace_artefacts(artefacts, spawn)
            state["phase_artefacts"].update(artefacts)
        elif key in {"hitl_required", "hitl_reason"}:
            continue
        elif key == "procedure_outcomes" and isinstance(value, dict):
            # Per procedure, latest wins: a re-dispatched phase replaces its own outcome.
            state.setdefault(key, {}).update(value)
        elif key in _ACCUMULATE_KEYS and isinstance(value, list):
            existing = state.get(key)
            if not isinstance(existing, list):
                existing = []
            state[key] = _dedup_accumulated(existing + value, key)
        else:
            state[key] = value
    if delta.get("hitl_required"):
        state["hitl_required"] = True
        state["hitl_reason"] = delta.get("hitl_reason")


__all__ = ["_apply_delta"]
