"""The production lookup path: a filtered scroll of the corpus on its ``ref`` payload field."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.regulatory_rag.lookup.annotate import annotate

#: Chunks to read before selecting: an article is split per unit by the
#: ingestion chunker, and ``chunk_total`` is small (single digits) for all but
#: the longest articles.
_SCROLL_LIMIT = 24


def qdrant_lookup(self, ref: str, top_k: int,
                  regulation: str) -> list[dict[str, Any]]:  # pragma: no cover
    """Scroll the corpus for every chunk whose payload ``ref`` equals *ref*.

    No vector is involved, so no embedding is computed and the provider guard
    is not consulted. Chunks are returned in ``chunk_index`` order — an article
    opens with its operative rule, and a citation check wants the beginning of
    the article rather than whichever fragment scored best.

    :param self: The :class:`RegulatoryRAG` holding the lazy Qdrant client.
    :param ref: Canonical reference to match exactly.
    :param top_k: Maximum chunks to return.
    :param regulation: Payload ``regulation`` to constrain the match to.
    :returns: Annotated hits, first chunk first.
    """
    from qdrant_client import models as qmodels

    from aaa.agents.tier1.regulatory_rag.clients import ensure_qdrant
    from aaa.agents.tier1.regulatory_rag.hits import _point_to_hit

    ensure_qdrant(self)
    records, _next = self._qdrant.scroll(
        collection_name=self._collection,
        scroll_filter=qmodels.Filter(must=[
            qmodels.FieldCondition(key="ref", match=qmodels.MatchValue(value=ref)),
            qmodels.FieldCondition(key="regulation",
                                   match=qmodels.MatchValue(value=regulation)),
        ]),
        limit=max(top_k, _SCROLL_LIMIT),
        with_payload=True,
    )
    ordered = sorted((_point_to_hit(r) for r in records),
                     key=lambda h: (h.get("chunk_index") is None, h.get("chunk_index") or 0))
    return [annotate(hit, ref, i) for i, hit in enumerate(ordered[:top_k], 1)]


__all__ = ["qdrant_lookup"]
