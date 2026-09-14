"""Idempotent Qdrant upserts (Step 6)."""
from __future__ import annotations

import hashlib
from typing import Any

from scripts.ingest_regulatory_corpus.chunker import batched
from scripts.ingest_regulatory_corpus.config import UPSERT_BATCH
from scripts.ingest_regulatory_corpus.deps import require
from scripts.ingest_regulatory_corpus.models import Chunk


def question_point_id(question_id: str) -> str:
    """Return the deterministic UUID string for an obligation-question point."""
    d = hashlib.sha256(question_id.encode("utf-8")).hexdigest()
    return f"{d[0:8]}-{d[8:12]}-{d[12:16]}-{d[16:20]}-{d[20:32]}"


def upsert_corpus_chunks(client: Any, collection: str, chunks: list[Chunk],
                         dense_vectors: list[list[float]],
                         sparse_vectors: list[dict[str, list]]) -> int:
    """Upsert chunks into the hybrid collection in batches.

    :returns: Number of points written.
    """
    qmodels = require("qdrant_client.models")
    written = 0
    for batch in batched(list(range(len(chunks))), UPSERT_BATCH):
        points = []
        for i in batch:
            sv = sparse_vectors[i]
            points.append(qmodels.PointStruct(
                id=chunks[i].point_id,
                payload={**chunks[i].payload, "text": chunks[i].text},
                vector={"dense": dense_vectors[i],
                        "sparse": qmodels.SparseVector(
                            indices=sv["indices"], values=sv["values"])},
            ))
        client.upsert(collection_name=collection, points=points, wait=True)
        written += len(points)
    return written


def upsert_obligation_questions(client: Any, collection: str,
                                questions: list[dict[str, Any]],
                                dense_vectors: list[list[float]]) -> int:
    """Upsert one point per compliance-checker question.

    :returns: Number of points written.
    """
    qmodels = require("qdrant_client.models")
    written = 0
    for batch in batched(list(range(len(questions))), UPSERT_BATCH):
        points = []
        for i in batch:
            q = questions[i]
            qid = q.get("question_id", "") or f"q{i}"
            points.append(qmodels.PointStruct(
                id=question_point_id(qid), payload=q, vector=dense_vectors[i]))
        client.upsert(collection_name=collection, points=points, wait=True)
        written += len(points)
    return written
