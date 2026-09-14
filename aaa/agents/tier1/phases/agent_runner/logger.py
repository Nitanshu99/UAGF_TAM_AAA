"""Part 1 of the former ``agent_runner`` module (auto-split)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _evidence_uris(state: dict) -> list[str]:
    """Accumulate the engagement's admitted evidence chain.

    Returns the MinIO URIs of every artefact persisted so far — intake first
    (T01a/T01b/T01c), then every prior-phase artefact in insertion order — so
    each phase's Verifier sees the growing evidence set and downstream phases can
    cite earlier artefacts. De-duplicated; empty/missing URIs are dropped.
    """
    artefacts = state.get("phase_artefacts", {})
    # Intake artefacts lead the list so the most foundational evidence is first.
    ordered_tids = [
        "T01a_stage_a_triage",
        "T01b_annex_iv_dossier",
        "T01c_intake_completeness_report",
        *artefacts.keys(),
    ]
    seen: set[str] = set()
    uris: list[str] = []
    for tid in ordered_tids:
        ref = artefacts.get(tid)
        uri = ref.get("uri", "") if isinstance(ref, dict) else ""
        if uri and uri not in seen:
            seen.add(uri)
            uris.append(uri)
    return uris


async def _invoke(agent: Any, dispatch: Any, timeout: int) -> Any:
    """Invoke agent.process() handling both running and non-running event loops.

    Uses an effective-timeout runner: a hung agent call cannot wedge the caller
    (the worker thread is abandoned on timeout rather than waited on). Binds
    the dispatch's engagement id so every LLM call this agent makes groups
    into one Langfuse session (best-effort — absent if undeclared), and the
    deadline that timeout implies, so the agent's ReAct loop can decline a
    retrieval round it has no time to finish (fix 18). Only the first branch
    below actually enforces *timeout*, so only it binds a deadline — the other
    two run unbounded, and a loop told otherwise would cut itself short against
    a limit nothing was going to apply.
    """
    from aaa.observability.trace_context import bind_engagement_id
    from aaa.platform.phase_budget import bind_phase_deadline
    engagement_id = (dispatch.get("declaration_summary") or {}).get("engagement_id") \
        if isinstance(dispatch, dict) else None
    with bind_engagement_id(engagement_id):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                from aaa.observability.tracing import drain_llm_callbacks
                from aaa.platform.async_timeout import run_coro_blocking

                # Finish this loop's queued LiteLLM callbacks before the hop: the worker
                # loop re-binds LiteLLM 1.86's global logging queue, and a callback still
                # in flight here then raised ``task_done() called too many times``
                # against it (T-20260913-083; reproduced on litellm 1.86.0).
                await drain_llm_callbacks()
                with bind_phase_deadline(timeout):
                    return run_coro_blocking(agent.process(dispatch), timeout=timeout)
            return loop.run_until_complete(agent.process(dispatch))
        except RuntimeError:
            return await agent.process(dispatch)


_ACCUMULATE_KEYS = {
    "blocking_findings",
    "positive_findings",
    "remediation_roadmap",
    "insufficient_evidence_articles",
}
