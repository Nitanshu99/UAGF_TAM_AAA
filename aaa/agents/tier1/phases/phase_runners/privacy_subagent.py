"""The tier-3 privacy spawn: a PII deep-dive extending T08."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris, run_agent_on_state
from aaa.platform.phase_budget import phase_timeout
from aaa.platform.state.artefact_keys import SPAWN_PRIVACY


async def run_privacy_subagent(agent: Any, state: dict) -> dict:
    """Run PrivacyDPOAgent tier-3 spawn; no-op on failure.

    ``stage_b`` is passed for the same reason Phase 2 and Phase 3 receive it —
    the PII deep-dive has to load the evaluation set to re-scan it; without a
    dataset the spawn scanned ``None`` and reported no PII found (P5).
    """
    if agent is None:
        return state
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="Privacy",
        task_brief="Privacy / DPO audit for GDPR compliance. Extend T08.",
        evidence_uris=_evidence_uris(state),
        output_contract="T08_special_category_data_log",
        declaration_summary={
            "engagement_id": eng,
            "modality": state.get("modality", "tabular"),
            "phase_artefacts": state.get("phase_artefacts", {}),
            "stage_b": state.get("client_submission", {}).get("stage_b", {}) or {},
        },
    )
    _, state = await run_agent_on_state(
        agent, dispatch, state,
        timeout=phase_timeout(getattr(agent, "name", None)), spawn=SPAWN_PRIVACY)
    return state


__all__ = ["run_privacy_subagent"]
