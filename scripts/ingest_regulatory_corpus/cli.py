"""Argument parsing for the ingestion CLI."""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.ingest_regulatory_corpus.config import (
    DEFAULT_CHECKER_PATH,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_COLLECTION,
    DEFAULT_CORPUS_DIR,
    DEFAULT_OBLIGATIONS_COLLECTION,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the ingestion CLI arguments.

    :param argv: Optional argument list (defaults to ``sys.argv[1:]``).
    :returns: Parsed namespace.
    """
    p = argparse.ArgumentParser(
        description="Ingest the regulatory corpus into Qdrant (hybrid dense + sparse).")
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS_DIR,
                   help="directory of HTML/PDF regulations")
    p.add_argument("--checker", type=Path, default=DEFAULT_CHECKER_PATH,
                   help="path to eu_ai_act_compliance_checker.json")
    p.add_argument("--collection", default=DEFAULT_COLLECTION,
                   help="Qdrant corpus collection name")
    p.add_argument("--obligations-collection", default=DEFAULT_OBLIGATIONS_COLLECTION,
                   help="Qdrant obligations index collection name")
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    p.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    p.add_argument("--dry-run", action="store_true",
                   help="parse + chunk + log counts only; no embedding calls, "
                        "no Qdrant writes")
    p.add_argument("--reset", action="store_true",
                   help="drop and recreate both collections before ingest")
    p.add_argument("--skip-obligations", action="store_true",
                   help="skip the obligations_index collection")
    p.add_argument("--force-reembed", action="store_true",
                   help="re-embed and overwrite ALL chunks even if they already exist "
                        "in Qdrant (default: skip chunks whose SHA-256 ID is present)")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)
