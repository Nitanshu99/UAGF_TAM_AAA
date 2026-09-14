"""One ReAct retrieval round: run the model's plan, merge what it pulled, re-ask.

A round stops the loop — returning ``None`` — when the reply is not a plan, when the
round would not fit the phase's remaining wall-clock budget (fix 18), when the plan
asked for nothing or returned nothing, or when nothing was learned that the model did
not already hold.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.evidence_retrieval.dedup import hit_keys, merge_hits
from aaa.tools.evidence_retrieval.envelope import plan_in
from aaa.tools.evidence_retrieval.logger import _run_plan_queries
from aaa.tools.evidence_retrieval.notice import terminal_block
from aaa.tools.evidence_retrieval.rounds import is_final_round, learned_something, round_fits
from aaa.tools.evidence_retrieval.timing import _timed

logger = logging.getLogger(__name__)


async def expand_one_round(agent: Any, prompt_name: str, payload: dict[str, Any],
                           result: dict[str, Any], costs: list[float], *,
                           reg_hits: list, client_hits: list, round_idx: int,
                           last: int, rag: Any, engagement_id: str, name: str):
    """Run one expansion round.

    :param agent: The phase agent.
    :param prompt_name: PROMPT.md section name.
    :param payload: The user payload as it currently stands.
    :param result: The model's latest reply.
    :param costs: Per-call durations, extended in place.
    :param reg_hits: Regulatory hits accumulated so far.
    :param client_hits: Client-document hits accumulated so far.
    :param round_idx: 1-based round number.
    :param last: The ceiling on rounds.
    :param rag: A ``RegulatoryRAG`` instance, or ``None``.
    :param engagement_id: Engagement id for ``client_doc_search``.
    :param name: Agent name, for the logs.
    :returns: ``(payload, result, reg_hits, client_hits)``, or ``None`` to stop.
    """
    # Q4: a plan the model sent bare — `{"regulatory_queries": [...]}` with
    # no wrapper — is still a request for retrieval, and used to be read as
    # an answer instead of executed.
    plan = plan_in(result)
    if plan is None:
        return None
    # Fix 18: the phase timeout covers every call below, and overrunning it
    # costs the whole report rather than the round (P4).
    if not round_fits(costs, name):
        return None
    reg_q, client_q, new_reg, new_client = _run_plan_queries(plan, rag, engagement_id)
    if (not reg_q and not client_q) or (not new_reg and not new_client):
        return None

    # F6: `hits += new_hits` injected the same chunk once per query that
    # matched it — 12 hits for 4 unique chunks at case 01 call #004.
    held = hit_keys(reg_hits) | hit_keys(client_hits)
    reg_hits, reg_dupes, reg_cut = merge_hits(reg_hits, new_reg)
    client_hits, client_dupes, client_cut = merge_hits(client_hits, new_client)
    if not learned_something(held, hit_keys(reg_hits) | hit_keys(client_hits), name):
        return None

    # The round the model is told is final has to be the one that turns out
    # to be last — the budget can close retrieval earlier than the ceiling,
    # and a deadline the model was never given is not one it can answer to.
    final = is_final_round(round_idx, last, costs)
    # `rerun_context` carries the Verifier critique that ordered this rerun
    # (F2); retrieval bookkeeping gets its own key rather than clobbering it.
    payload = {
        **payload,
        "regulatory_hits": reg_hits,
        "client_doc_hits": client_hits,
        "retrieval_expansion": terminal_block(
            round_idx, reg_q, client_q, final=final),
    }
    logger.info(
        "%s: ReAct round %d/%d pulled %d regulatory + %d client-doc chunk(s); "
        "injected %d + %d after dropping %d duplicate(s) and %d over cap.",
        name, round_idx, last, len(new_reg), len(new_client),
        len(reg_hits), len(client_hits), reg_dupes + client_dupes, reg_cut + client_cut,
    )
    result = await _timed(agent, prompt_name, payload, costs)
    return payload, result, reg_hits, client_hits


__all__ = ["expand_one_round"]
