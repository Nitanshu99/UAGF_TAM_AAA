"""LLM synthesis step for Phase 1 (ReAct prompt over the computed evidence)."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.scope_agent.errors import _PROMPT_NAME
from aaa.agents.tier2.tools_run import tools_run
from aaa.tools.evidence_retrieval import (
    acompletion_json_react,
    seed_client_doc_hits,
    seed_regulatory_hits,
)

logger = logging.getLogger(__name__)

#: The phase's subject-matter questions, as authored. This anchor names four
#: references and the corpus returned two of them (Art. 5 and Annex III missed,
#: Art. 23 returned unasked-for); fix 17 fetches all four by identifier.
_DOC_QUERY = "declared modality risk tier Annex III intended purpose Art 5"
_RAG_QUERY = ("Article 6 classification high-risk Annex III Article 5 prohibited "
              "practices Article 43 conformity assessment")


def gather_context(agent: Any, decl: dict, engagement_id: str) -> tuple[list, list]:
    """Collect client-document and regulatory retrieval hits for the prompt."""
    client_doc_hits: list[dict[str, Any]] = []
    if decl.get("client_doc_collection"):
        client_doc_hits = seed_client_doc_hits(engagement_id, _DOC_QUERY, decl)
    regulatory_hits = seed_regulatory_hits(agent.rag, _RAG_QUERY)
    return client_doc_hits, regulatory_hits


async def run_llm_synthesis(agent: Any, message: dict, decl: dict, engagement_id: str,
                            computed_evidence: dict, client_doc_hits: list,
                            regulatory_hits: list) -> tuple[str | None, str]:
    """Run the Phase 1 prompt; returns ``(llm_summary, prompt_note)``.

    Falls back to the deterministic path (summary ``None``) when the LLM
    call fails for any reason.
    """
    llm_payload: dict[str, Any] = {}
    llm_fallback_mode = True
    try:
        llm_payload = await acompletion_json_react(
            agent, _PROMPT_NAME,
            {
                "task": message.get("task_brief")
                or "Execute Phase 1 declaration verification per the Phase 1 Protocol.",
                "evidence_uris": message.get("evidence_uris", []),
                "declaration_summary": decl,
                "client_doc_hits": client_doc_hits,
                "regulatory_hits": regulatory_hits,
                "rerun_context": message.get("rerun_context"),
                "computed_evidence": computed_evidence,
                "tools_executed": tools_run("P1", client_docs=bool(client_doc_hits)),
            },
            # Fix 42: the keys this caller reads two lines below are its
            # output contract, asserted at the answer position instead of
            # discovered as an empty `.get()` after the reply is filed.
            contract=("summary", "rationale_summary"),
            rag=agent.rag, engagement_id=engagement_id,
        )
        llm_fallback_mode = False
    except Exception as exc:  # noqa: BLE001 — any LLM failure falls back
        logger.warning("ScopeAgent prompt runtime failed (%s); using deterministic fallback.", exc)
    prompt_note = agent.prompt_note(_PROMPT_NAME, llm_fallback_mode)
    llm_summary = llm_payload.get("summary") or llm_payload.get("rationale_summary")
    return llm_summary, prompt_note
