"""document_evidence — answer artefact fields from the provider's own documents, verbatim.

Every tier-2 agent retrieved the client's uploaded documents, but only its LLM
narrative saw them: no deterministic builder used a single passage, so datasheet,
model-card and monitoring fields stayed empty or null while the provider's technical
documentation, model card and monitoring plan answered them (T-20260913-041).

A field is filled only from a passage that contains the question's required terms,
and it carries the quote and its source; otherwise it stays null. Retrieval ranks,
the terms decide, the quote shows the reader what was relied on. Declared Stage B
fields are searched first, as the dossier contract.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Iterable

from aaa.tools.document_evidence.ground import (
    DATE_RANGE,
    DENIALS,
    DOSSIER,
    NEGATIONS,
    PERIODS,
    Evidence,
    Question,
)
from aaa.tools.document_evidence.select import ground

logger = logging.getLogger(__name__)

Search = Callable[..., list[dict[str, Any]]]
#: Passages retrieved per question. The terms, not the rank, decide; a wider net
#: costs nothing in precision and finds the table row ranked sixth.
TOP_K = 8
#: Uploaded files that are data the audit measures, not the provider's account of its
#: system. Case 04's golden evaluation set holds the legal corpus the system answers
#: from, and a GDPR Art. 6(1) excerpt in it was quoted as the datasheet's consent
#: mechanism (MiniMax run, 2026-09-14).
DATA_ROLES = frozenset({"golden_set"})


def searchable(decl: dict[str, Any], engagement_id: str) -> str:
    """The engagement whose documents may be searched, or "" when none were ingested.

    :param decl: Declaration summary; ``client_doc_collection`` says ingestion ran.
    :param engagement_id: Engagement identifier.
    """
    return engagement_id if decl.get("client_doc_collection") else ""


def gather_evidence(engagement_id: str, questions: Iterable[Question],
                    declared: dict[str, Any] | None = None,
                    search: Search | None = None) -> dict[str, Evidence | None]:
    """Search the dossier once per question and keep only grounded answers.

    :param engagement_id: Engagement whose client documents are searched ("" skips).
    :param questions: What to look for.
    :param declared: Stage B text fields, searched as passages ahead of documents.
    :param search: ``client_doc_search``-compatible callable; the real one by default.
    :returns: ``{question key: Evidence or None}``.
    """
    if search is None:
        from aaa.tools.client_doc_ingest import client_doc_search as search  # noqa: N811
    dossier = [{"text": str(v), "source_uri": f"{DOSSIER}{k}", "score": 2.0}
               for k, v in (declared or {}).items() if isinstance(v, str) and v.strip()]
    results: dict[str, Evidence | None] = {}
    for question in questions:
        hits = [hit for hit in (search(engagement_id, question.query, top_k=TOP_K)
                                if engagement_id else [])
                if hit.get("document_role") not in DATA_ROLES]
        results[question.key] = ground(dossier + hits, question)
    grounded = sorted(key for key, evidence in results.items() if evidence)
    logger.info("document_evidence: %d of %d question(s) grounded %s (documents searched: %s).",
                len(grounded), len(results), grounded, bool(engagement_id))
    return results


__all__ = ["DATA_ROLES", "DATE_RANGE", "DENIALS", "DOSSIER", "Search", "NEGATIONS", "PERIODS", "TOP_K", "Evidence", "Question",
           "gather_evidence", "ground", "searchable"]
