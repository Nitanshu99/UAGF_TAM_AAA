"""Per-unit sentence chunking (Step 2)."""
from __future__ import annotations

from typing import Any, Iterable

from scripts.ingest_regulatory_corpus.checker import CheckerLookup
from scripts.ingest_regulatory_corpus.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from scripts.ingest_regulatory_corpus.deps import require
from scripts.ingest_regulatory_corpus.models import Chunk, Unit


def batched(seq: list[Any], size: int) -> Iterable[list[Any]]:
    """Yield *seq* in fixed-size batches."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def chunk_units(
    units: list[Unit],
    checker: CheckerLookup,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Run ``SentenceSplitter`` *per unit* so chunks never cross legal boundaries.

    :param units: Structural units from the loaders.
    :param checker: Compliance-checker lookup for payload enrichment.
    :param chunk_size: SentenceSplitter chunk size.
    :param chunk_overlap: SentenceSplitter chunk overlap.
    :returns: Enriched chunks ready for embedding.
    """
    li_node_parser = require("llama_index.core.node_parser", "llama-index")
    li_schema = require("llama_index.core.schema", "llama-index")
    splitter = li_node_parser.SentenceSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[Chunk] = []
    for unit in units:
        nodes = splitter.get_nodes_from_documents([li_schema.Document(text=unit.text)])
        enrich = checker.for_ref(unit.ref)
        for i, node in enumerate(nodes):
            chunks.append(Chunk(
                text=node.get_content(),
                payload={
                    "regulation": unit.regulation,
                    "kind": unit.kind,
                    "ref": unit.ref,
                    "title": unit.title,
                    "source_file": unit.source_file,
                    "chunk_index": i,
                    "chunk_total": len(nodes),
                    "obligations": enrich["obligations"],
                    "entity_types": enrich["entity_types"],
                    "risk_classes": enrich["risk_classes"],
                },
            ))
    return chunks
