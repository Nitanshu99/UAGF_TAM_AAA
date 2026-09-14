"""Phase-id → awaitable runner mapping for ReAct DISPATCH execution.

Every runner already builds its own Dispatch and passes through
``run_phase_with_verification`` (the non-bypassable Verifier gate), so the
LLM chooses *which phase when* while the mechanics stay identical to the
graph runtime.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aaa.agents.tier1.phases.phase_runners import (
    run_cyber_subagent,
    run_phase_1,
    run_phase_2,
    run_phase_3,
    run_phase_4,
    run_phase_5,
    run_phase_6,
    run_privacy_subagent,
    run_uagf_tam_l,
)
from aaa.integrations.dispatch import apply_provider_evidence

Runner = Callable[[dict[str, Any], dict], Awaitable[dict]]


async def _phase_5(agents: dict[str, Any], state: dict) -> dict:
    """Phase 5 plus the provider-evidence landing the graph node performs.

    :param agents: Agent registry from ``initialise_agents``.
    :type agents: dict[str, Any]
    :param state: The mutable AuditState dict.
    :type state: dict
    :returns: Updated state.
    :rtype: dict
    """
    state = await run_phase_5(agents.get("governance_agent"), state)
    return apply_provider_evidence(state)


RUNNERS: dict[str, Runner] = {
    "P1": lambda a, s: run_phase_1(a.get("scope_agent"), s),
    "P2": lambda a, s: run_phase_2(a.get("data_auditor"), s),
    "P3": lambda a, s: run_phase_3(a.get("model_validator"), s),
    "P4": lambda a, s: run_phase_4(a.get("output_fairness"), s),
    "P5": _phase_5,
    "P6": lambda a, s: run_phase_6(a.get("report_architect"), s, a.get("client_brief")),
    "L": lambda a, s: run_uagf_tam_l(a.get("uagf_tam_l"), s),
    "CYBER": lambda a, s: run_cyber_subagent(a.get("cyber_agent"), s),
    "PRIVACY": lambda a, s: run_privacy_subagent(a.get("privacy_agent"), s),
}
