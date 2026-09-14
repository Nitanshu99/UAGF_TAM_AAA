"""Retrieval context for Phase 2: prompt hits, and the datasheet's document evidence."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.dataset import dataset_role
from aaa.agents.tier2.data_auditor.t06 import t06_questions
from aaa.tools.document_evidence import Evidence, gather_evidence, searchable
from aaa.tools.evidence_retrieval import seed_client_doc_hits, seed_regulatory_hits

#: The phase's subject-matter questions, as authored. Fix 17 widened what they
#: reach without editing either: the anchor's named articles are additionally
#: fetched by identifier, and the declaration supplies a second client-doc query.
_DOC_QUERY = "data governance training data quality missingness class balance PII policy"
_RAG_QUERY = ("Article 10 data and data governance training validation testing data "
              "quality bias representativeness special category data")


def gather_context(agent: Any, decl: dict, engagement_id: str) -> tuple[list, list]:
    """Collect client-document and regulatory retrieval hits for the prompt."""
    client_doc_hits: list[dict[str, Any]] = []
    if decl.get("client_doc_collection"):
        client_doc_hits = seed_client_doc_hits(engagement_id, _DOC_QUERY, decl)
    regulatory_hits = seed_regulatory_hits(agent.rag, _RAG_QUERY)
    return client_doc_hits, regulatory_hits


def gather_t06_evidence(decl: dict, engagement_id: str,
                        t01b: dict) -> dict[str, Evidence | None]:
    """Answer the datasheet questions about the dataset Phase 2 examined.

    :param decl: Declaration summary (whether documents were ingested, Stage B).
    :param engagement_id: Engagement identifier.
    :param t01b: Annex IV dossier, whose text fields are searched first.
    """
    questions = t06_questions(dataset_role(t01b, decl))
    return gather_evidence(searchable(decl, engagement_id), questions,
                           declared=decl.get("stage_b") or t01b)


__all__ = ["gather_context", "gather_t06_evidence"]
