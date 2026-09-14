"""Half of finding F15 — a retrieval plan is not an answer.

``acompletion_json_react`` ran a bounded expansion: the model may emit a
``retrieval_plan``, the runtime executes it and re-invokes the model with the
hits appended.  Nothing ever told the model that the re-invocation was its
*last*, and nothing rejected a plan-shaped reply in the terminal position — the
loop simply exited and returned it.  Case 01 hit this twice.  At call #009 the
DataAuditor planned instead of answering and its planning reply became the Phase
2 artefact, so the ``num_instances = 0`` defect the Verifier had localised was
never addressed.  At call #035 the ReportArchitect returned
``{"artefact_uri": "", "summary": "", "report_signed": true,
"retrieval_plan": {...}}`` — a signed report that was a to-do list.

Two changes, and the first is what makes the second fair:

*Say so.*  :data:`TERMINAL_NOTICE` is stamped into the payload's
``retrieval_expansion`` block on the final round, so the model is told in terms
that no further retrieval will run and that it must answer from what it has.  A
model cannot be held to a deadline it was never given — that is the same
reasoning fix 4 applied to the Orchestrator's inexpressible HITL instruction.

*Then hold to it.*  :func:`close_retrieval` re-prompts **once** with retrieval
explicitly closed, and raises :class:`RetrievalPlanNotAnsweredError` if the reply
still carries a plan.  Every phase agent already wraps its LLM synthesis in
``except Exception`` → deterministic fallback, so the phase closes loudly (an
``ERROR`` in the trail, ``llm_fallback_mode=true`` stamped into every artefact
it emits) instead of quietly filing a plan as evidence.
"""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.evidence_retrieval.closing_payload import closing_payload
from aaa.tools.evidence_retrieval.contract import OutputContractNotMetError, contract_unmet
from aaa.tools.evidence_retrieval.envelope import (
    RetrievalPlanNotAnsweredError,
    _not_an_answer,
    plan_in,
    unwrap_tool_envelope,
)
from aaa.tools.evidence_retrieval.logger import logger
from aaa.tools.evidence_retrieval.notice import TERMINAL_NOTICE, terminal_block


async def close_retrieval(agent: Any, prompt_name: str, payload: dict[str, Any],
                          result: Any, contract: Sequence[str] = ()) -> dict[str, Any]:
    """Return an *answer*, re-prompting once when the reply is not one.

    :param agent: The phase agent (provides ``acompletion_json`` + ``name``).
    :param prompt_name: PROMPT.md section name for the agent.
    :param payload: The payload the model was last given.
    :param result: The model's reply.
    :param contract: Keys the caller will read the answer from (fix 42). Empty
        asserts nothing, which is what a caller with no declared contract gets.
    :raises RetrievalPlanNotAnsweredError: The re-prompt returned a plan again.
    :raises OutputContractNotMetError: The re-prompt still met no contract key.
    :returns: The reply, without ``retrieval_plan``.
    """
    name = getattr(agent, "name", "agent")
    unwrapped = unwrap_tool_envelope(result, contract)
    if unwrapped is not result:
        logger.warning(
            "%s: the reply wrapped its artefact in a %r tool call; the payload "
            "meets the output contract, so it is filed as the answer and the "
            "tool name is discarded (the runtime assembles tool calls itself).",
            name, result.get("tool"))
        result = unwrapped
    reason = _not_an_answer(result, contract)
    if reason is None:
        return result if isinstance(result, dict) else {}
    logger.error(
        "%s: the reply is not the artefact it was asked for — %s. Re-prompting "
        "once with retrieval closed and the contract stated.", name, reason)
    closed = closing_payload(payload, contract)
    retry = unwrap_tool_envelope(await agent.acompletion_json(prompt_name, closed),
                                 contract)
    again = _not_an_answer(retry, contract)
    if again is not None:
        logger.error("%s: the closing re-prompt also failed — %s. No artefact is "
                     "filed from this reply.", name, again)
        if plan_in(retry) is not None:
            raise RetrievalPlanNotAnsweredError(
                f"{name} returned a retrieval_plan after retrieval was closed")
        raise OutputContractNotMetError(f"{name}: {again}")
    logger.info("%s: answered on the closing re-prompt.", name)
    return {k: v for k, v in (retry or {}).items() if k != "retrieval_plan"}




__all__ = ["TERMINAL_NOTICE", "RetrievalPlanNotAnsweredError",
           "OutputContractNotMetError", "contract_unmet", "plan_in",
           "unwrap_tool_envelope", "terminal_block", "close_retrieval"]
