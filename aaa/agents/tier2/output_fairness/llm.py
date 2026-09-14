"""LLM synthesis for Phase 4 with deterministic fallback."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.output_fairness.context import LlmSynthesis, SuiteResult
from aaa.agents.tier2.tools_run import tools_run
from aaa.tools.evidence_retrieval import acompletion_json_react, seed_regulatory_hits

logger = logging.getLogger(__name__)

PROMPT_NAME = "phase4_output"

# Fix 47 re-attributed the fairness verdict from Art. 15 §1 (accuracy, robustness
# and cybersecurity) to the articles that actually require a bias examination,
# but left this retrieval query naming the wrong one. The mismatch is
# measurable: on the Mariposa engagement the re-ranker returned nothing above
# the relevance boundary (best 0.00), so the phase reasoned over passages that
# did not answer it. The query now names the same articles as
# ``verdicts.FINDING_ARTICLES``.
_RAG_QUERY = ("Article 10 paragraph 2 point (f) examination of possible biases "
              "Article 9 risk management non-discrimination fairness across groups")


async def run_llm_synthesis(
    agent: Any,
    message: dict[str, Any],
    decl: dict[str, Any],
    engagement_id: str,
    suite: SuiteResult,
    tox_result: dict[str, Any],
) -> LlmSynthesis:
    """Ask the LLM to synthesise the Phase 4 evidence into a narrative.

    Falls back to the deterministic tool outputs when the call fails.

    :param agent: The calling :class:`OutputFairnessTester` instance.
    :param message: Original dispatch message.
    :param decl: Declaration summary from the dispatch.
    :param engagement_id: Engagement identifier.
    :param suite: Fairness suite result.
    :param tox_result: ``toxicity_classifier`` result.
    :returns: :class:`LlmSynthesis` with summary and prompt note.
    """
    regulatory_hits = seed_regulatory_hits(agent.rag, _RAG_QUERY)
    payload: dict[str, Any] = {}
    fallback = True
    try:
        payload = await acompletion_json_react(
            agent, PROMPT_NAME,
            {"task": message.get("task_brief")
             or "Execute Phase 4 fairness testing per the Phase 4 Protocol.",
             "evidence_uris": message.get("evidence_uris", []),
             "declaration_summary": decl,
             "regulatory_hits": regulatory_hits,
             "rerun_context": message.get("rerun_context"),
             "tool_outputs": {"demographic_parity": suite.dp,
                              "equal_opportunity": suite.eo,
                              "disparate_impact": suite.di,
                              "subgroup_metrics": suite.sg,
                              "toxicity_results": tox_result,
                              "overall_verdict": suite.overall_verdict},
             "tools_executed": tools_run("P4")},
            # Fix 42: the keys this caller reads below are its output
            # contract, asserted at the answer position instead of
            # discovered as an empty `.get()` after the reply is filed.
            contract=("summary", "rationale_summary"),
            rag=agent.rag, engagement_id=engagement_id)
        fallback = False
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("OutputFairnessTester prompt runtime failed (%s); "
                       "using deterministic fallback.", exc)
    return LlmSynthesis(
        summary=payload.get("summary") or payload.get("rationale_summary"),
        prompt_note=agent.prompt_note(PROMPT_NAME, fallback))
