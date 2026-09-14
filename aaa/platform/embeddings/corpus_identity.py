"""Record which embedding model built a vector corpus, and read it back.

Dimensionality alone cannot tell two same-width models apart, and that swap is
the dangerous one: nothing errors, the search simply returns confidently-ranked
nonsense. Stamping the provider identity at ingest turns it into a refusal.

The stamp lives in a sibling collection, not as a point inside the corpus. A
sentinel point in the searched collection would rank into real results unless
every query carried a filter to exclude it — a cost paid on every search to
store one record.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

#: Suffix of the sibling collection holding the identity record.
META_SUFFIX = "__embedding_meta"

_POINT_ID = 1


def meta_collection(collection: str) -> str:
    """Return the name of the sibling collection holding *collection*'s stamp.

    :param collection: Corpus collection name.
    :type collection: str
    :returns: Sibling metadata collection name.
    :rtype: str
    """
    return f"{collection}{META_SUFFIX}"


def stamp_identity(client: Any, collection: str, purpose: str) -> None:
    """Record the embedder that built *collection*.

    Best-effort: a stamp that cannot be written must not abort an otherwise
    successful ingest, since the guard degrades safely when it is absent.

    :param client: A Qdrant client.
    :type client: Any
    :param collection: Corpus collection just written.
    :type collection: str
    :param purpose: Embedding purpose that produced the vectors.
    :type purpose: str
    """
    from qdrant_client import models as qmodels

    from aaa.platform.embeddings import embedding_dim, embedding_identity

    name = meta_collection(collection)
    payload = {
        "model_id": embedding_identity(purpose),
        "dim": embedding_dim(purpose),
        "purpose": purpose,
        "stamped_at": datetime.now(timezone.utc).isoformat(),
    }
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=1, distance=qmodels.Distance.COSINE),
        )
    client.upsert(collection_name=name, points=[
        qmodels.PointStruct(id=_POINT_ID, vector=[0.0], payload=payload)])


def read_identity(client: Any, collection: str) -> dict | None:
    """Return *collection*'s identity stamp, or ``None`` when unstamped.

    ``None`` covers both a corpus ingested before stamping existed and an
    unreachable metadata collection. Neither is evidence of a mismatch, so
    callers must not treat it as one.

    :param client: A Qdrant client.
    :type client: Any
    :param collection: Corpus collection name.
    :type collection: str
    :returns: The stamp payload, or ``None``.
    :rtype: dict | None
    """
    try:
        points = client.retrieve(
            collection_name=meta_collection(collection),
            ids=[_POINT_ID], with_payload=True)
        return dict(points[0].payload) if points and points[0].payload else None
    except Exception:  # noqa: BLE001 — absent or unreadable both mean "unknown"
        return None
