"""LangGraph invocation for the offline/CI fallback (bound in agent.py via runner)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.sequential import run_sequential


async def _run_langgraph(self, state: dict, graph: Any | None = None) -> dict:  # pragma: no cover
    """Invoke the compiled LangGraph; return the final state."""
    config = {"configurable": {"thread_id": state["engagement_id"]}}
    final: dict = {}
    graph = graph or self._graph
    if graph is None:
        return run_sequential(self._agents, state)
    async for chunk in graph.astream(state, config=config):
        final = chunk
    if len(final) == 1:
        maybe_state = next(iter(final.values()))
        if isinstance(maybe_state, dict) and "engagement_id" in maybe_state:
            return maybe_state
    return final
