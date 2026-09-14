"""Defaults, environment bootstrap and shared constants for the ingester."""
from __future__ import annotations

import os
from pathlib import Path

# Load .env from the repo root early so the provider keys etc. are available
# without the caller having to manually `source .env` in the shell.
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except ImportError:
    pass  # python-dotenv not installed; env vars must be set externally

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CORPUS_DIR = REPO_ROOT / "data" / "regulatory_corpus"
DEFAULT_CHECKER_PATH = REPO_ROOT / "data" / "eu_ai_act_compliance_checker.json"
DEFAULT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "regulatory_corpus")
DEFAULT_OBLIGATIONS_COLLECTION = "obligations_index"

#: Historic name of the dense model; the provider seam now owns the choice.
DENSE_MODEL = "text-embedding-3-large"


def dense_dim() -> int:
    """Return the corpus vector width, from the configured query embedder.

    A function, not a constant: resolving it at import time would construct the
    provider — loading a sentence-transformers model merely to read this module.
    Sharing one source of truth with query time is what stops the corpus being
    written at a width the searcher cannot match.

    :returns: Dense-vector width for the regulatory corpus.
    :rtype: int
    """
    from aaa.platform.embeddings import embedding_dim

    return embedding_dim("regulatory")
SPARSE_MODEL = "Qdrant/bm25"

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100
EMBED_BATCH = 64
UPSERT_BATCH = 128

#: Corpus payload keys that get a Qdrant keyword index.
FILTER_KEYS = ("regulation", "kind", "ref", "obligations",
               "entity_types", "risk_classes", "source_file")

REGULATION_BY_STEM = {
    "EU_AI_Act": "EU_AI_Act",
    "GDPR": "GDPR",
}

PDF_REGULATION_BY_NAME = {
    "ISO:IEC 42001-2023.pdf": "ISO_IEC_42001",
    "isae_3000.pdf": "ISAE 3000",
    "iso_19011.pdf": "ISO 19011",
}

REQUIRED_STANDARD_PDFS = {
    "isae_3000.pdf": "ISAE 3000 (Revised)",
    "iso_19011.pdf": "ISO 19011:2018",
}

COVERAGE_PROBE_QUERIES = [
    "ISAE 3000 assurance engagement objectives reasonable assurance",
    "ISO 19011 audit programme planning audit criteria",
]

# EUR-Lex HTML uses these classes/ids consistently across regulations.
EURLEX_ARTICLE_DIV = "eli-subdivision"
EURLEX_ARTICLE_TITLE = "oj-ti-art"      # e.g. "Article 9"
EURLEX_ARTICLE_SUBTITLE = "oj-sti-art"  # e.g. "Risk management system"
EURLEX_RECITAL_ID_PREFIX = "rct_"
EURLEX_ARTICLE_ID_PREFIX = "art_"
EURLEX_ANNEX_ID_PREFIX = "anx_"
