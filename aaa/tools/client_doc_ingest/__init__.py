"""Per-engagement client-document ingestion and search for Phase agents.

Documents are chunked locally, embedded with OpenAI ``text-embedding-3-large``
(3072 dimensions), and stored in a dense-only Qdrant collection named
``client_docs_{engagement_id}``.  Calls without documents or credentials are
safe no-ops so tests and demo runs do not need Qdrant or OpenAI access.
"""
from __future__ import annotations

from aaa.tools.client_doc_ingest.config import (
    ClientDocIngestError,
    _embeddings_available,  # noqa: F401 (test access)
)
from aaa.tools.client_doc_ingest.core import client_doc_ingest
from aaa.tools.client_doc_ingest.extract import _extract_docx_pages  # noqa: F401 (shared)
from aaa.tools.client_doc_ingest.loading import _coerce_bytes  # noqa: F401 (shared)
from aaa.tools.client_doc_ingest.search import client_doc_search

__all__ = ["ClientDocIngestError", "client_doc_ingest", "client_doc_search"]
