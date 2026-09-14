"""Hybrid-search configuration (must match scripts/ingest_regulatory_corpus.py)."""
from __future__ import annotations

_DENSE_MODEL = "text-embedding-3-large"
_SPARSE_MODEL = "Qdrant/bm25"
_DENSE_VECTOR_NAME = "dense"
_SPARSE_VECTOR_NAME = "sparse"
_PREFETCH_LIMIT = 32  # candidates per branch before RRF fusion
