"""LLM synthesis for Phase 3 with deterministic fallback."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.model_validator.context import Explainability, LlmSynthesis
from aaa.agents.tier2.model_validator.payload import phase3_payload
from aaa.agents.tier2.model_validator.queries import _DOC_QUERY, _RAG_QUERY, PROMPT_NAME
from aaa.tools.evidence_retrieval import (
    acompletion_json_react,
    seed_client_doc_hits,
    seed_regulatory_hits,
)

logger = logging.getLogger(__name__)




async def run_llm_synthesis(
    agent: Any,
    message: dict[str, Any],
    decl: dict[str, Any],
    engagement_id: str,
    metrics_result: dict[str, Any],
    expl: Explainability,
    robustness_result: dict[str, Any],
) -> LlmSynthesis:
    """Ask the LLM to synthesise the Phase 3 evidence into a narrative.

    Falls back to the deterministic tool outputs when the call fails.

    :param agent: The calling :class:`ModelValidator` instance.
    :param message: Original dispatch message.
    :param decl: Declaration summary from the dispatch.
    :param engagement_id: Engagement identifier.
    :param metrics_result: Output of ``metric_suite``.
    :param expl: Explainability evidence from step 3.
    :param robustness_result: Output of ``robustness_probe``.
    :returns: :class:`LlmSynthesis` with summary, prompt note and doc hits.
    """
    client_doc_hits: list[dict[str, Any]] = []
    if decl.get("client_doc_collection"):
        client_doc_hits = seed_client_doc_hits(engagement_id, _DOC_QUERY, decl)
    regulatory_hits = seed_regulatory_hits(agent.rag, _RAG_QUERY)
    payload, fallback = {}, True
    try:
        payload = await acompletion_json_react(
            agent, PROMPT_NAME,
            phase3_payload(message, decl, client_doc_hits, regulatory_hits,
                           metrics_result, expl, robustness_result),
            # Fix 42: the keys this caller reads below are its output
            # contract, asserted at the answer position instead of
            # discovered as an empty `.get()` after the reply is filed.
            contract=("summary", "rationale_summary"),
            rag=agent.rag, engagement_id=engagement_id)
        fallback = False
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("ModelValidator prompt runtime failed (%s); "
                       "using deterministic fallback.", exc)
    return LlmSynthesis(
        summary=payload.get("summary") or payload.get("rationale_summary"),
        prompt_note=agent.prompt_note(PROMPT_NAME, fallback),
        client_doc_hits=client_doc_hits)
