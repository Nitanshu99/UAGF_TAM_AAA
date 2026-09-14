"""Part 2 of the former ``evidence_retrieval`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.evidence_retrieval.dedup import merge_hits
from aaa.tools.evidence_retrieval.expand_round import expand_one_round
from aaa.tools.evidence_retrieval.logger import (  # noqa: F401
    _MAX_QUERIES_PER_KIND,
    _TOP_K,
    _clean_queries,
    _run_plan_queries,
    logger,
)
from aaa.tools.evidence_retrieval.rounds import MAX_ROUNDS
from aaa.tools.evidence_retrieval.seed import seed_regulatory_hits  # noqa: F401
from aaa.tools.evidence_retrieval.terminal_round import close_retrieval
from aaa.tools.evidence_retrieval.timing import _timed
from aaa.tools.evidence_retrieval.tool_requests import check_tool_requests


async def acompletion_json_react(
    agent: Any,
    prompt_name: str,
    payload: dict[str, Any],
    *,
    rag: Any = None,
    engagement_id: str = "",
    rounds: int = MAX_ROUNDS,
    contract: Sequence[str] = (),
) -> dict[str, Any]:
    """Run ``agent.acompletion_json`` with bounded ``retrieval_plan`` expansion.

    *rounds* is a ceiling, not a count. Fix 18 raised it from one — a single
    chance to correct a missed retrieval — and made the loop stop early when a
    round would not fit the phase's remaining wall-clock budget, or when the
    previous one returned nothing the model did not already hold. Both gates are
    in :mod:`~aaa.tools.evidence_retrieval.rounds`; the reason the raise is safe
    is that they, not the number, decide.

    :param agent: The phase agent (provides ``acompletion_json`` + ``name``).
    :param prompt_name: PROMPT.md section name for the agent.
    :param payload: The user payload; may already carry ``regulatory_hits`` /
        ``client_doc_hits`` which are extended in place across rounds.
    :param rag: A ``RegulatoryRAG`` instance (or ``None``).
    :param engagement_id: Engagement id for ``client_doc_search`` ("" disables).
    :param rounds: Max retrieval-plan expansion rounds (clamped at 0). Phase 6
        passes 0 deliberately: it composes from admitted artefacts and has no
        retrieval channel of its own.
    :param contract: Fix 42 — the keys this caller will read its answer from.
        Asserted **positively** at the answer position: a reply carrying none of
        them is re-prompted once with the contract stated and then refused, so
        the caller's ``except`` records ``llm_fallback_mode`` instead of filing a
        tool request as the artefact. Empty asserts nothing.
    :raises RetrievalPlanNotAnsweredError: The model kept planning after retrieval closed.
    :raises OutputContractNotMetError: The reply met no contract key twice.
    :returns: The final parsed JSON result from the model.
    """
    name = getattr(agent, "name", "agent")
    costs: list[float] = []
    result = await _timed(agent, prompt_name, payload, costs)
    # F6: seeds come from one query each so they cannot collide, but ranking them
    # here means the accumulated list is ordered by score from the first round on.
    reg_hits, _, _ = merge_hits([], list(payload.get("regulatory_hits") or []))
    client_hits, _, _ = merge_hits([], list(payload.get("client_doc_hits") or []))
    last = max(0, rounds)

    for round_idx in range(1, last + 1):
        expanded = await expand_one_round(
            agent, prompt_name, payload, result, costs,
            reg_hits=reg_hits, client_hits=client_hits,
            round_idx=round_idx, last=last, rag=rag,
            engagement_id=engagement_id, name=name)
        if expanded is None:
            break
        payload, result, reg_hits, client_hits = expanded


    # F15: the loop used to return whatever the terminal pass produced, so a
    # reply that was still a plan became the phase's artefact.
    answer = await close_retrieval(agent, prompt_name, payload, result, contract)
    # F10: `tool_calls` is not a request channel — a tool named here never ran.
    return check_tool_requests(answer, payload, name)


__all__ = ["acompletion_json_react", "seed_regulatory_hits"]
