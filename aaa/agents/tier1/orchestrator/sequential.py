"""Sequential pipeline fallback used when LangGraph is absent."""
from __future__ import annotations

import asyncio
from typing import Any

from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.node_stubs import node_hitl_checkpoint, node_route
from aaa.agents.tier1.phases.nodes.plan import node_plan
from aaa.agents.tier1.phases.nodes.stage0 import node_stage0
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
from aaa.platform.async_timeout import run_coro_blocking


async def _pipeline(agents: dict[str, Any], s: dict) -> dict:
    """Run all pipeline nodes in order."""
    s = node_stage0(s)
    s = node_plan(s)
    s = await run_phase_1(agents.get("scope_agent"), s)
    s = node_route(s)
    if s.get("_branch") == "l_branch":
        s = await run_uagf_tam_l(agents.get("uagf_tam_l"), s)
    else:
        s = await run_phase_2(agents.get("data_auditor"), s)
        s = await run_phase_3(agents.get("model_validator"), s)
        s = await run_phase_4(agents.get("output_fairness"), s)
    s = await run_phase_5(agents.get("governance_agent"), s)
    if agents.get("cyber_agent"):
        s = await run_cyber_subagent(agents["cyber_agent"], s)
    if agents.get("privacy_agent"):
        s = await run_privacy_subagent(agents["privacy_agent"], s)
    s = apply_provider_evidence(s)
    s = node_compliance_matrix(s)
    s = node_hitl_checkpoint(s)
    # Always emit a provisional report; HITL cases are deferred, not blocking.
    return await run_phase_6(agents.get("report_architect"), s,
                             agents.get("client_brief"))


def run_sequential(agents: dict[str, Any], state: dict) -> dict:
    """Execute the full pipeline synchronously and return the final state.

    :param agents: Phase agents keyed by role.
    :param state: Initial AuditState.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return run_coro_blocking(_pipeline(agents, state), timeout=900)
        return loop.run_until_complete(_pipeline(agents, state))
    except RuntimeError:
        return asyncio.run(_pipeline(agents, state))
