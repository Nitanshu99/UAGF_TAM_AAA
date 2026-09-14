"""Per-field context retrieval from the engagement's document collection."""
from __future__ import annotations

from typing import Any

from aaa.agents.doc_intelligence.queries import FIELD_QUERIES


def gather_field_contexts(engagement_id: str) -> dict[str, dict[str, Any]]:
    """Search the engagement collection once per extractable field.

    :param engagement_id: Engagement whose Qdrant collection is searched.
    :returns: Field → ``{context, best_source, best_score}`` for every field
        with at least one hit.
    """
    from aaa.tools.client_doc_ingest import client_doc_search
    field_contexts: dict[str, dict[str, Any]] = {}
    for field, query in FIELD_QUERIES.items():
        hits = client_doc_search(engagement_id, query, top_k=3)
        if hits:
            field_contexts[field] = {
                "context": "\n\n".join(h["text"] for h in hits[:3]),
                "best_source": (f"{hits[0].get('source_uri', 'doc')} "
                                f"p.{hits[0].get('page_number', '?')}"),
                "best_score": float(hits[0].get("score", 0.0)),
            }
    return field_contexts
