"""Creating an engagement's collection must record which model indexed it.

Without this the guard has nothing to compare and silently degrades to the
width-only check — so the stamp write is tested against a recording double
rather than assumed, since every other guard test supplies a stamp ready-made.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.embeddings.corpus_identity import meta_collection
from aaa.tools.client_doc_ingest.qdrant import _ensure_collection

_COLLECTION = "client_docs_eng_1"


class _RecordingQdrant:
    """Qdrant double recording collection creation and upserts."""

    def __init__(self) -> None:
        self.created: list[str] = []
        self.upserts: dict[str, Any] = {}

    def collection_exists(self, collection_name: str) -> bool:
        """Report whether *collection_name* has been created here."""
        return collection_name in self.created

    def create_collection(self, collection_name: str, **kwargs: Any) -> None:
        """Record the creation."""
        del kwargs
        self.created.append(collection_name)

    def create_payload_index(self, **kwargs: Any) -> None:
        """Accept payload-index creation."""

    def upsert(self, collection_name: str, points: Any) -> None:
        """Record the upserted payload."""
        self.upserts[collection_name] = points[0].payload


def test_ensure_collection_stamps_the_embedding_model():
    """The identity lands in the sibling metadata collection."""
    client = _RecordingQdrant()

    _ensure_collection(client, _COLLECTION)

    meta = meta_collection(_COLLECTION)
    assert meta in client.upserts, "no identity stamp written at ingest"
    assert client.upserts[meta]["model_id"] == "openai:text-embedding-3-large"
    assert client.upserts[meta]["purpose"] == "client_docs"


def test_stamp_records_the_width_used_to_build_the_collection():
    """dim is stored so an unstamped-vs-stamped comparison stays meaningful."""
    client = _RecordingQdrant()

    _ensure_collection(client, _COLLECTION)

    assert client.upserts[meta_collection(_COLLECTION)]["dim"] == 3072
