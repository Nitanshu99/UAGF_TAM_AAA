"""Sync LangGraph node wrappers around the async phase runners."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.phase_runners import (
    run_phase_1,
    run_phase_2,
    run_phase_3,
    run_phase_4,
    run_phase_5,
    run_phase_6,
    run_uagf_tam_l,
)
from aaa.integrations.dispatch import apply_provider_evidence
from aaa.platform.async_timeout import run_coro_blocking


def node_phase_1(agents: dict[str, Any], state: dict) -> dict:
    """Sync wrapper — delegates to async run_phase_1 via thread pool."""
    return run_coro_blocking(run_phase_1(agents.get("scope_agent"), state), timeout=180)


def node_parallel_phases(agents: dict[str, Any], state: dict) -> dict:
    """Sync LangGraph wrapper for Phases 2–4 / L-branch."""
    async def _run(s: dict) -> dict:
        if s.get("_branch") == "l_branch":
            return await run_uagf_tam_l(agents.get("uagf_tam_l"), s)
        s = await run_phase_2(agents.get("data_auditor"), s)
        s = await run_phase_3(agents.get("model_validator"), s)
        return await run_phase_4(agents.get("output_fairness"), s)

    # P2→P3→P4 run sequentially in this node; each phase now seeds a regulatory
    # retrieval and may issue a bounded ReAct re-invocation, so the combined budget
    # must accommodate three LLM-heavy phases plus their retrieval round-trips.
    return run_coro_blocking(_run(state), timeout=600)


def node_phase_5(agents: dict[str, Any], state: dict) -> dict:
    """Sync LangGraph wrapper for Phase 5 (GovernanceAgent).

    Also lands the XAI / security evidence documents after Phase 5, so the
    internal adapters can reference every produced artefact (T09–T15).
    """
    state = run_coro_blocking(run_phase_5(agents.get("governance_agent"), state), timeout=300)
    return apply_provider_evidence(state)


def node_phase_6(agents: dict[str, Any], state: dict) -> dict:
    """Sync LangGraph wrapper for Phase 6 (ReportArchitect, then the client brief).

    The 240 s ceiling funded the ReportArchitect alone. The brief that follows it
    makes one call per audited requirement, so the wrapper has to allow for both
    or it cancels the brief mid-write every time.
    """
    from aaa.agents.tier1.phases.phase_runners.client_brief_step import brief_timeout
    return run_coro_blocking(
        run_phase_6(agents.get("report_architect"), state, agents.get("client_brief")),
        timeout=240 + brief_timeout(state))
