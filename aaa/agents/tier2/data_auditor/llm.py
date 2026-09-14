"""LLM synthesis step for Phase 2 (ReAct prompt over the tool outputs)."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.data_auditor.errors import _PROMPT_NAME
from aaa.agents.tier2.tools_run import tools_run
from aaa.tools.evidence_retrieval import acompletion_json_react

logger = logging.getLogger(__name__)

async def run_llm_synthesis(agent: Any, message: dict, decl: dict, engagement_id: str,
                            tool_outputs: dict, client_doc_hits: list,
                            regulatory_hits: list) -> tuple[str | None, str]:
    """Run the Phase 2 prompt; returns ``(llm_summary, prompt_note)``."""
    llm_payload: dict[str, Any] = {}
    llm_fallback_mode = True
    try:
        llm_payload = await acompletion_json_react(
            agent, _PROMPT_NAME,
            {
                "task": message.get("task_brief")
                or "Execute Phase 2 data governance audit per the Phase 2 Protocol.",
                "evidence_uris": message.get("evidence_uris", []),
                "declaration_summary": decl,
                "client_doc_hits": client_doc_hits,
                "regulatory_hits": regulatory_hits,
                "rerun_context": message.get("rerun_context"),
                "tool_outputs": tool_outputs,
                "tools_executed": tools_run("P2", client_docs=bool(client_doc_hits)),
            },
            # Fix 42: the keys this caller reads below are its output
            # contract, asserted at the answer position instead of
            # discovered as an empty `.get()` after the reply is filed.
            contract=("summary", "rationale_summary"),
            rag=agent.rag, engagement_id=engagement_id,
        )
        llm_fallback_mode = False
    except Exception as exc:  # noqa: BLE001 — any LLM failure falls back
        logger.warning("DataAuditor prompt runtime failed (%s); using deterministic fallback.", exc)
    prompt_note = agent.prompt_note(_PROMPT_NAME, llm_fallback_mode)
    llm_summary = llm_payload.get("summary") or llm_payload.get("rationale_summary")
    return llm_summary, prompt_note
