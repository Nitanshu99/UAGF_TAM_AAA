"""Constants, error type, and naming helpers for client-document ingestion."""
from __future__ import annotations

import os
import re
from pathlib import PurePosixPath

from aaa.settings import settings

_VECTOR_NAME = "dense"
_CHUNK_CHARS = 1600
_OVERLAP_CHARS = 200
_EMBED_BATCH = 64
_UPSERT_BATCH = 128


class ClientDocIngestError(Exception):
    """Raised when client-document ingestion fails unexpectedly."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"[client_doc_ingest] {reason}")


def _dense_dim() -> int:
    """Return the vector width of the configured client-docs embedder.

    Resolved at call time rather than as a constant: the collection must be
    created at whatever width the selected provider actually emits (3072 for
    OpenAI's large model, 384 or 768 for typical sentence-transformers), and a
    module-level constant would also force the model to load on import.

    :returns: Dimensionality of client-document vectors.
    :rtype: int
    """
    from aaa.platform.embeddings import embedding_dim

    return embedding_dim("client_docs")


def _openai_api_key() -> str:
    """Resolve the OpenAI key from the environment or settings."""
    return os.environ.get("OPENAI_API_KEY") or settings.openai_api_key


def _embeddings_available() -> bool:
    """True when client-document embedding is possible.

    Answered by the provider that owns the ``client_docs`` purpose: a local
    model needs no key, OpenAI and OpenRouter each need their own, and gating
    on ``OPENAI_API_KEY`` alone reported ingestion unavailable on exactly the
    configurations that never use that key.

    :returns: Whether embeddings can be produced for client documents.
    :rtype: bool
    """
    from aaa.platform.embeddings import credentials_present, provider_for

    if provider_for("client_docs") == "openai":
        return bool(_openai_api_key())
    return credentials_present("client_docs")


def _collection_name(engagement_id: str) -> str:
    """Build the per-engagement Qdrant collection name."""
    safe = re.sub(r"[^A-Za-z0-9_]", "_", engagement_id.replace("-", "_"))
    return f"client_docs_{safe}"


def _filename(uri: str) -> str:
    """Extract the filename from an artefact URI."""
    return PurePosixPath(uri.split("?", 1)[0]).name or "client_document"


def _content_type(uri: str) -> str:
    """Infer the document content type from the URI suffix."""
    suffix = PurePosixPath(uri.split("?", 1)[0]).suffix.lower().lstrip(".")
    return suffix if suffix in {"pdf", "docx", "txt", "json", "md"} else "txt"
