"""Idempotency helpers: discovering points already present in Qdrant."""
from __future__ import annotations

from typing import Any

from scripts.ingest_regulatory_corpus.upsert import question_point_id


def filter_new_questions(questions: list[dict[str, Any]],
                         existing_ids: set[str]) -> list[dict[str, Any]]:
    """Return only questions whose point ID is not already in *existing_ids*."""
    return [q for q in questions
            if question_point_id(q.get("question_id", "") or "") not in existing_ids]


def fetch_existing_ids(client: Any, collection: str) -> set[str]:
    """Return the set of all point IDs already stored in *collection*.

    Uses ``scroll`` with no filter to page through every record.  Only the
    ID is fetched (``with_payload=False``, ``with_vectors=False``) so this is
    fast and cheap even for large collections.  Returns an empty set if the
    collection does not yet exist.
    """
    try:
        existing: set[str] = set()
        offset = None
        while True:
            result, next_offset = client.scroll(
                collection_name=collection, offset=offset, limit=1000,
                with_payload=False, with_vectors=False)
            for point in result:
                existing.add(str(point.id))
            if next_offset is None:
                break
            offset = next_offset
        return existing
    except Exception:  # collection missing or connection error  # pragma: no cover
        return set()
