"""Execution methods for the Orchestrator (bound in agent.py).

Production mode is the ReAct loop — the Orchestrator model decides the
sequencing. The LangGraph DAG and the sequential runner remain only as the
labelled offline/CI fallback per PROMPT.md ("deterministic stubs are allowed
only for explicit offline/CI fallback").
"""
from __future__ import annotations

import logging
import os

from aaa.agents.tier1.checkpointer import make_async_checkpointer
from aaa.agents.tier1.orchestrator.langgraph_run import (
    _run_langgraph,  # noqa: F401  # re-exported for agent.py
)
from aaa.agents.tier1.orchestrator.sequential import run_sequential
from aaa.observability.trace_context import bind_engagement_id
from aaa.observability.tracing import flush_llm_tracing

logger = logging.getLogger(__name__)


def _react_enabled() -> bool:
    """True when the LLM-driven ReAct loop should drive the engagement.

    ``AAA_ORCHESTRATION_MODE`` (``react`` | ``graph``) wins when set;
    otherwise ReAct is on whenever a provider key is available.
    """
    mode = os.environ.get("AAA_ORCHESTRATION_MODE", "").strip().lower()
    if mode in {"react", "graph"}:
        return mode == "react"
    return any(os.environ.get(k) for k in
               ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "NVIDIA_NIM_API_KEY",
                "NVIDIA_API_KEY"))


async def run(self, state: dict) -> dict:
    """Execute the ReAct loop, or the deterministic fallback when offline.

    Binds the engagement id for the whole run. Every entry point — API, CLI and
    wizard — reaches the pipeline through this method, so binding here attributes
    the Orchestrator's own ReAct turns, the Verifier's critiques and the wrap-up
    rescue, none of which pass through ``agent_runner._invoke`` (finding F7), and
    a future entry point cannot forget to do it.
    """
    # F4 (S3): stamped here rather than in either branch below, so the fact
    # travels with the state whichever runtime executes it and whatever the run
    # goes on to do. `run_integrity` reads it at deliverable-write time.
    state["unwired_agents"] = list(getattr(self, "_unwired", []) or [])
    with bind_engagement_id(state.get("engagement_id")):
        try:
            return await _run(self, state)
        finally:
            # The run's traces must be complete when the run returns: a CLI or
            # mock-case process exits right after this, and LiteLLM's queued
            # Langfuse callbacks would otherwise die with the interpreter.
            await flush_llm_tracing()


async def _run(self, state: dict) -> dict:
    """Dispatch to the ReAct loop or the deterministic fallback."""
    if _react_enabled():
        from aaa.agents.tier1.orchestrator.react.loop import run_react
        logger.info("Orchestration mode: react (LLM-driven sequencing).")
        return await run_react(self, self._agents, state)
    logger.info("Orchestration mode: graph (offline/CI deterministic fallback).")
    try:
        async with make_async_checkpointer() as checkpointer:
            await checkpointer.setup()
            graph = self._build_graph(checkpointer=checkpointer)
            if graph is not None:
                return await self._run_langgraph(state, graph)
    except Exception as exc:
        logger.warning(
            "AsyncPostgresSaver unavailable (%s); falling back to uncheckpointed graph.",
            exc)
    if self._graph is not None:
        return await self._run_langgraph(state)
    return run_sequential(self._agents, state)
