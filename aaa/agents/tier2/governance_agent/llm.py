"""LLM synthesis step for Phase 5 (ReAct prompt over the CGSA evidence)."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.governance_agent.errors import PROMPT_NAME
from aaa.agents.tier2.governance_agent.payload_slim import slim_cgsa_payload
from aaa.agents.tier2.tools_run import tools_run
from aaa.tools.cgsa_ingest import IngestResult
from aaa.tools.evidence_retrieval import acompletion_json_react

logger = logging.getLogger(__name__)


async def run_llm_synthesis(
    agent: Any,
    message: dict[str, Any],
    decl: dict[str, Any],
    engagement_id: str,
    payload: Any,
    result: IngestResult,
    spawn: dict[str, Any],
    client_doc_hits: list[dict[str, Any]],
    regulatory_hits: list[dict[str, Any]],
) -> tuple[str | None, str]:
    """Run the Phase 5 prompt and return ``(llm_summary, prompt_note)``.

    Falls back to the deterministic path (summary ``None``) when the LLM
    call fails for any reason.

    :param agent: The GovernanceAgent instance (provides prompt runtime).
    :param message: Full dispatch message.
    :param decl: Declaration summary.
    :param engagement_id: Engagement identifier.
    :param payload: Raw CGSA payload.
    :param result: Validated ingest result.
    :param spawn: Tier-3 spawn decisions.
    :param client_doc_hits: Client-document retrieval hits.
    :param regulatory_hits: Regulatory-RAG retrieval hits.
    :returns: LLM summary (or ``None``) and the provenance prompt note.
    """
    llm_payload: dict[str, Any] = {}
    llm_fallback_mode = True
    try:
        llm_payload = await acompletion_json_react(
            agent, PROMPT_NAME,
            {
                "task": message.get("task_brief")
                or "Execute Phase 5 governance review per the Phase 5 Protocol.",
                "evidence_uris": message.get("evidence_uris", []),
                "declaration_summary": decl,
                "client_doc_hits": client_doc_hits,
                "regulatory_hits": regulatory_hits,
                "rerun_context": message.get("rerun_context"),
                "cgsa_payload": slim_cgsa_payload(payload),
                # Without the nested copy of `payload` that `_build_state_delta`
                # puts there for the *state*. Sent whole, the Phase 5 prompt
                # carried the CGSA assessment twice: on the 2026-09-09 Mariposa
                # run that was 287,079 characters of which 105,887 were a
                # duplicate, inside a 403,778-character user message — 101,237
                # tokens, 39% of this model's declared window, on one call. The
                # agent needs the 38-control detail to write T14/T15 and still
                # has it; only the second copy is gone (‑48%).
                "ingest_state_delta": {k: v for k, v in result.state_delta.items()
                                       if k != "cgsa_payload"},
                "spawn_recommendations": spawn,
                "tools_executed": tools_run("P5", client_docs=bool(client_doc_hits)),
            },
            # Fix 42: the keys this caller reads below are its output
            # contract, asserted at the answer position instead of
            # discovered as an empty `.get()` after the reply is filed.
            contract=("summary", "phase5_narrative_summary"),
            rag=agent.rag, engagement_id=engagement_id,
        )
        llm_fallback_mode = False
    except Exception as exc:  # noqa: BLE001 — any LLM failure falls back
        logger.warning(
            "GovernanceAgent prompt runtime failed (%s); using deterministic fallback.", exc)
    prompt_note = agent.prompt_note(PROMPT_NAME, llm_fallback_mode)
    llm_summary = llm_payload.get("summary") or llm_payload.get("phase5_narrative_summary")
    return llm_summary, prompt_note
