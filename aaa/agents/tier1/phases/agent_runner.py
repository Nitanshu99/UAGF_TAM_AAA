"""
aaa.agents.tier1.phases.agent_runner — Shared async agent invocation helper.

Provides ``run_agent_on_state(agent, dispatch, state, timeout)`` which:

1. Runs ``agent.process(dispatch)`` in an asyncio-safe way (handles both
   running and non-running event loops via a thread-pool executor).
2. Applies the ``declaration_verification_delta`` from the Report back
   onto the mutable *state* dict.
3. Returns the updated state (or the original state on failure).
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _evidence_uris(state: dict) -> list[str]:
    """Extract T01a + T01b URIs from phase_artefacts."""
    artefacts = state.get("phase_artefacts", {})
    uris = [
        artefacts.get("T01a_stage_a_triage", {}).get("uri", ""),
        artefacts.get("T01b_annex_iv_dossier", {}).get("uri", ""),
    ]
    return [u for u in uris if u]


async def _invoke(agent: Any, dispatch: Any, timeout: int) -> Any:
    """Invoke agent.process() handling both running and non-running event loops."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, agent.process(dispatch))
                return future.result(timeout=timeout)
        return loop.run_until_complete(agent.process(dispatch))
    except RuntimeError:
        return await agent.process(dispatch)


def _apply_delta(state: dict, delta: dict) -> None:
    """Merge a declaration_verification_delta onto the mutable AuditState."""
    for key, value in delta.items():
        if key == "phase_artefacts":
            state["phase_artefacts"].update(value or {})
        elif key in {"hitl_required", "hitl_reason"}:
            continue
        else:
            state[key] = value
    if delta.get("hitl_required"):
        state["hitl_required"] = True
        state["hitl_reason"] = delta.get("hitl_reason")


async def run_agent_on_state(
    agent: Any,
    dispatch: Any,
    state: dict,
    timeout: int = 180,
) -> tuple[Any, dict]:
    """Run *agent* with *dispatch*, apply delta to *state*, return (report, state).

    Returns (None, state) if the agent raises an exception — callers
    can fall back to stub behaviour.
    """
    try:
        report = await _invoke(agent, dispatch, timeout)
        delta = report.get("declaration_verification_delta", {})
        _apply_delta(state, delta)
        return report, state
    except Exception as exc:
        logger.warning(
            "%s.process() failed (%s); caller should fall back to stub.",
            type(agent).__name__,
            exc,
        )
        return None, state


__all__ = ["run_agent_on_state", "_evidence_uris"]
