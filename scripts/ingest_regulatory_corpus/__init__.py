"""Hybrid (dense + sparse) Qdrant ingestion of the regulatory corpus.

Feeds the Tier-1 RegulatoryRAG (§3.1 #3, §10).

Pipeline
--------
0. Pre-load ``data/eu_ai_act_compliance_checker.json`` → build the
   article → {obligations, entity_types, risk_classes} lookup used to
   enrich each chunk's payload.
1. Loaders — BeautifulSoup for EUR-Lex HTML (EU AI Act, GDPR), pypdfium2
   for the standards PDFs.  Each loader yields *structural units*
   (article, recital, annex, clause, control) — never raw text.
2. Chunker — ``SentenceSplitter`` applied **per unit** so chunks never
   cross an article boundary.
3. Dense embeddings — the ``regulatory`` provider from ``EMBEDDINGS_REGULATORY``
   (``openai`` or ``openrouter``: ``text-embedding-3-large``, dim=3072;
   ``local``: the sentence-transformers model named in ``EMBEDDINGS_LOCAL_MODEL``).
4. Sparse embeddings — fastembed BM25 (``Qdrant/bm25``) for hybrid search.
5. Qdrant collections — ``regulatory_corpus`` (hybrid) and
   ``obligations_index`` (dense-only questionnaire mirror).
6. Idempotent upsert keyed by SHA-256 of the chunk text.

Usage::

    python -m scripts.ingest_regulatory_corpus [--dry-run] [--reset]

Required env vars: the configured provider's key — ``OPENAI_API_KEY`` or
``OPENROUTER_API_KEY`` (skipped in ``--dry-run``), ``QDRANT_URL`` (default
``http://localhost:6333``), optional ``QDRANT_API_KEY``.
"""
from __future__ import annotations

from scripts.ingest_regulatory_corpus.checker import CheckerLookup
from scripts.ingest_regulatory_corpus.checker.build import build_checker_lookup
from scripts.ingest_regulatory_corpus.chunker import chunk_units
from scripts.ingest_regulatory_corpus.dispatch import discover_corpus, load_units_for_path
from scripts.ingest_regulatory_corpus.embed import dense_embed, sparse_embed
from scripts.ingest_regulatory_corpus.html_loader import load_html_units
from scripts.ingest_regulatory_corpus.isae_loader import load_isae_3000_units
from scripts.ingest_regulatory_corpus.iso.loader import load_pdf_units
from scripts.ingest_regulatory_corpus.main import main
from scripts.ingest_regulatory_corpus.models import Chunk, Unit

__all__ = [
    "Chunk", "CheckerLookup", "Unit", "build_checker_lookup", "chunk_units",
    "dense_embed", "discover_corpus", "load_html_units", "load_isae_3000_units",
    "load_pdf_units", "load_units_for_path", "main", "sparse_embed",
]
