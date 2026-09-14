"""Corpus-loading and summary helpers for the pipeline stages."""
from __future__ import annotations

from pathlib import Path

from scripts.ingest_regulatory_corpus.console import ok, warn
from scripts.ingest_regulatory_corpus.dispatch import discover_corpus, load_units_for_path
from scripts.ingest_regulatory_corpus.models import Chunk, Unit


def load_all_units(corpus_dir: Path) -> list[Unit]:
    """Discover the corpus directory and dispatch to the right loader.

    :param corpus_dir: Directory containing the regulation sources.
    :returns: All structural units across the corpus.
    """
    units: list[Unit] = []
    for path, regulation, _kind in discover_corpus(corpus_dir):
        loaded = load_units_for_path(path, regulation)
        if loaded:
            ok(f"loaded {len(loaded):4d} units from {path.name} ({regulation})")
        else:
            warn(f"loaded    0 units from {path.name} ({regulation}) — check parser/format")
        units.extend(loaded)
    return units


def summarise(chunks: list[Chunk]) -> dict[str, int]:
    """Count chunks per ``regulation/kind`` bucket.

    :param chunks: Chunks produced by the chunker.
    :returns: Bucket → count mapping.
    """
    counts: dict[str, int] = {}
    for c in chunks:
        key = f"{c.payload['regulation']}/{c.payload['kind']}"
        counts[key] = counts.get(key, 0) + 1
    return counts
