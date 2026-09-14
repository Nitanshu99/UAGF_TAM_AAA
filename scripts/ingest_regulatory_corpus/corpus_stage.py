"""Embed-and-upsert stage for corpus chunks (Steps 4–5)."""
from __future__ import annotations

from typing import Any

from scripts.ingest_regulatory_corpus.collections import ensure_corpus_collection
from scripts.ingest_regulatory_corpus.console import ok, warn
from scripts.ingest_regulatory_corpus.embed import dense_embed, sparse_embed
from scripts.ingest_regulatory_corpus.existing import fetch_existing_ids
from scripts.ingest_regulatory_corpus.models import Chunk
from scripts.ingest_regulatory_corpus.upsert import upsert_corpus_chunks


def ingest_corpus(args: Any, client: Any, chunks: list[Chunk]) -> None:
    """Embed and upsert corpus chunks, skipping already-present ones.

    :param args: Parsed CLI namespace.
    :param client: Qdrant client.
    :param chunks: All chunks produced by the chunker.
    """
    ensure_corpus_collection(client, args.collection, reset=args.reset)
    if args.force_reembed:
        new_chunks = chunks
        warn("--force-reembed: embedding ALL chunks (ignoring existing Qdrant points)")
    else:
        existing_ids = fetch_existing_ids(client, args.collection)
        new_chunks = [c for c in chunks if c.point_id not in existing_ids]
        skipped = len(chunks) - len(new_chunks)
        if skipped:
            ok(f"skip {skipped} chunks already in Qdrant "
               f"(re-run with --force-reembed to overwrite)")
        if not new_chunks:
            ok("all chunks already present — nothing to embed")
    dense: list[list[float]] = []
    sparse: list[dict[str, list]] = []
    if new_chunks:
        chunk_texts = [c.text for c in new_chunks]
        dense = dense_embed(chunk_texts)
        ok(f"dense vectors: {len(dense)} × {len(dense[0]) if dense else 0}")
        sparse = sparse_embed(chunk_texts)
        ok(f"sparse vectors: {len(sparse)}")
    written = upsert_corpus_chunks(client, args.collection, new_chunks, dense, sparse)
    ok(f"upserted {written} new points into '{args.collection}'")
