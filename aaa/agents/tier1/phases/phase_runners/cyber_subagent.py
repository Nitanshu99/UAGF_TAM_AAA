"""Part 10 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris, run_agent_on_state
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p3 import run_phase_3  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p4 import run_phase_4  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p5 import run_phase_5  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p6 import run_phase_6  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase6_declaration_summary import (  # noqa: F401
    _phase6_declaration_summary,
)
from aaa.agents.tier1.phases.phase_runners.privacy_subagent import run_privacy_subagent
from aaa.agents.tier1.phases.phase_runners.uagf_tam_l import run_uagf_tam_l  # noqa: F401
from aaa.platform.phase_budget import phase_timeout
from aaa.platform.state.artefact_keys import SPAWN_CYBER


async def run_cyber_subagent(agent: Any, state: dict) -> dict:
    """Run CyberSecurityAgent tier-3 spawn; no-op on failure.

    The dispatch carries ``phase_artefacts`` because the brief says *extend
    T11*: without them the agent read an empty dict and rebuilt the artefact
    from nothing (P5). ``spawn`` keeps whatever it produces out of Phase 3's
    slot.
    """
    if agent is None:
        return state
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="Cyber",
        task_brief="Cybersecurity and adversarial robustness audit. Extend T11.",
        evidence_uris=_evidence_uris(state),
        output_contract="T11_robustness_report",
        declaration_summary={
            "engagement_id": eng,
            "modality": state.get("modality", "tabular"),
            "phase_artefacts": state.get("phase_artefacts", {}),
            # The specialist adversarial probe needs the model and evaluation
            # set, which no dispatch has ever carried — so it ran on `None`.
            "stage_b": state.get("client_submission", {}).get("stage_b", {}) or {},
        },
    )
    _, state = await run_agent_on_state(
        agent, dispatch, state,
        timeout=phase_timeout(getattr(agent, "name", None)), spawn=SPAWN_CYBER)
    return state




__all__ = [
    "run_phase_1", "run_phase_2", "run_phase_3", "run_phase_4",
    "run_phase_5", "run_phase_6", "run_uagf_tam_l",
    "run_cyber_subagent", "run_privacy_subagent",
]
