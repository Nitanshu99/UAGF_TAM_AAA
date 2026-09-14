"""Construction of the RegulatoryRAG instance served to every phase agent.

Every entry point that builds an :class:`~aaa.agents.tier1.orchestrator.Orchestrator`
must pass one.  Without it ``seed_regulatory_hits`` and ``_run_plan_queries``
return no passages, and each agent's only model of the Regulation becomes the
partial article list in its static preamble — while its prompt still orders it
to ground citations in retrieved law.
"""
from __future__ import annotations

import logging

from aaa.agents.tier1.regulatory_rag.agent import RegulatoryRAG

logger = logging.getLogger(__name__)


def build_regulatory_rag() -> RegulatoryRAG | None:
    """Construct the shared RegulatoryRAG.

    Construction is cheap: Qdrant, OpenAI and the BM25 encoder are all
    initialised lazily on the first ``search()``, and an unreachable corpus
    degrades to the built-in KB rather than raising.

    :returns: A ``RegulatoryRAG``, or ``None`` if it could not be constructed
        (logged as an error — agents then run without regulatory grounding).
    """
    try:
        rag = RegulatoryRAG()
    except Exception as exc:  # noqa: BLE001 - a run must not die on RAG setup
        logger.error(
            "RegulatoryRAG could not be constructed (%s); agents will run with "
            "no retrieved law and must not be trusted on article scope.", exc)
        return None
    logger.info("RegulatoryRAG ready (collection=%s).", rag.collection)
    return rag


__all__ = ["build_regulatory_rag"]
