"""Retrieval-context gathering for Phase 5 (client docs + regulatory RAG)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.t15 import T15_QUESTIONS
from aaa.tools.document_evidence import Evidence, gather_evidence, searchable
from aaa.tools.evidence_retrieval import seed_client_doc_hits, seed_regulatory_hits

#: The phase's subject-matter questions, as authored. This anchor names four
#: articles and the corpus returned three — Article 9, which ``T14`` is
#: accountable for, was the one it dropped; fix 17 fetches it by identifier.
_DOC_QUERY = "monitoring logging post-market QMS risk management governance controls"
_RAG_QUERY = ("Article 9 risk management Article 17 quality management system "
              "Article 12 record-keeping logging Article 72 post-market monitoring")


def gather_context(agent: Any, decl: dict[str, Any], engagement_id: str,
                   ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect client-document and regulatory retrieval hits for the prompt.

    :param agent: GovernanceAgent instance (provides the RAG handle).
    :param decl: Declaration summary.
    :param engagement_id: Engagement identifier.
    :returns: ``(client_doc_hits, regulatory_hits)``.
    """
    client_doc_hits: list[dict[str, Any]] = []
    if decl.get("client_doc_collection"):
        client_doc_hits = seed_client_doc_hits(engagement_id, _DOC_QUERY, decl)
    regulatory_hits = seed_regulatory_hits(agent.rag, _RAG_QUERY)
    return client_doc_hits, regulatory_hits


def gather_t15_evidence(decl: dict[str, Any], engagement_id: str,
                        t01b: dict[str, Any]) -> dict[str, Evidence | None]:
    """Answer the T15 questions from the dossier fields and the uploaded documents.

    :param decl: Declaration summary (says whether a client collection exists).
    :param engagement_id: Engagement identifier.
    :param t01b: Annex IV dossier, whose text fields are searched first.
    """
    return gather_evidence(searchable(decl, engagement_id), T15_QUESTIONS, declared=t01b)
