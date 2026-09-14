"""Source-existence check against a Qdrant collection."""
from __future__ import annotations

from typing import Any


def _source_exists(client: Any, collection: str, source_uri: str) -> bool:
    """True when at least one point for *source_uri* is already indexed."""
    from qdrant_client import models as qmodels

    points, _ = client.scroll(
        collection_name=collection,
        scroll_filter=qmodels.Filter(
            must=[qmodels.FieldCondition(
                key="source_uri", match=qmodels.MatchValue(value=source_uri),
            )]
        ),
        limit=1,
        with_payload=False,
        with_vectors=False,
    )
    return bool(points)
