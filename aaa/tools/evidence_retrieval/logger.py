"""Part 1 of the former ``evidence_retrieval`` module (auto-split)."""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.client_doc_ingest import client_doc_search

logger = logging.getLogger(__name__)


_MAX_QUERIES_PER_KIND = 4


_TOP_K = 3


def _no_rag(context: str) -> None:
    """Report an unwired RegulatoryRAG — an unusable-evidence condition, not a nicety.

    Returning no law silently is what let an agent treat the abridged article
    list in its static preamble as the whole Regulation, so this is logged at
    ``ERROR`` and names the retrieval that was dropped.

    :param context: What was being retrieved when the RAG turned out to be absent.
    """
    logger.error(
        "No RegulatoryRAG wired: %s returns no law. Agents are grounded only in the "
        "static preamble, which is a partial index — treat any conclusion about "
        "article scope or existence as unevidenced.", context)


def _clean_queries(raw: Any) -> list[str]:
    """Normalise a model-proposed query list into clean, bounded strings."""
    if not isinstance(raw, (list, tuple)):
        return []
    cleaned = [q.strip() for q in raw if isinstance(q, str) and q.strip()]
    return cleaned[:_MAX_QUERIES_PER_KIND]


def _run_plan_queries(plan: dict[str, Any], rag: Any, engagement_id: str,
                      ) -> tuple[list[str], list[str], list[Any], list[Any]]:
    """Execute one round of retrieval-plan queries (never raises).

    :param plan: The model-proposed ``retrieval_plan`` block.
    :param rag: RegulatoryRAG instance or ``None``.
    :param engagement_id: Engagement id for client-doc search ("" disables).
    :returns: ``(reg_queries, client_queries, new_reg_hits, new_client_hits)``.
    """
    reg_q = _clean_queries(plan.get("regulatory_queries"))
    client_q = _clean_queries(plan.get("client_doc_queries"))
    new_reg: list[Any] = []
    new_client: list[Any] = []
    if reg_q and rag is None:
        _no_rag(f"{len(reg_q)} planned regulatory quer(y/ies) {reg_q}")
    for query in reg_q:
        if rag is not None:
            try:
                new_reg.extend(rag.search(query, top_k=_TOP_K))
            except Exception as exc:  # noqa: BLE001 - retrieval must not crash a phase
                logger.warning("ReAct regulatory search failed (%s): %s", query, exc)
    for query in client_q:
        if engagement_id:
            try:
                new_client.extend(client_doc_search(engagement_id, query, top_k=_TOP_K))
            except Exception as exc:  # noqa: BLE001
                logger.warning("ReAct client_doc search failed (%s): %s", query, exc)
    return reg_q, client_q, new_reg, new_client
