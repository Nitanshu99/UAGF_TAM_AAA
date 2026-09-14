"""Step 8: the regulatory corpus into Qdrant, only when it is not there already."""
from __future__ import annotations

import os
from pathlib import Path

from scripts.setup.console import ok, warn
from scripts.setup.shell import run

COLLECTION = "regulatory_corpus"


def corpus_state() -> tuple[str, int, str]:
    """What Qdrant holds under the corpus collection, against the configured embedder.

    :returns: ``(state, points, identity)`` — state is ``absent``, ``current``
        (stamped by the embedder this process would use) or ``stale``.
    """
    from qdrant_client import QdrantClient

    from aaa.platform.embeddings import embedding_identity
    from aaa.platform.embeddings.corpus_identity import read_identity

    want = embedding_identity("regulatory")
    collection = os.environ.get("QDRANT_COLLECTION", COLLECTION)
    client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
    if not client.collection_exists(collection):
        return "absent", 0, want
    points = int(client.count(collection).count)
    stamp = read_identity(client, collection) or {}
    return ("current" if stamp.get("model_id") == want else "stale"), points, want


def ingest_corpus(python: Path, skip: bool, reset: bool) -> None:
    """Run the ingester unless the corpus is already current.

    A collection stamped by a different embedder — the ``--mock-llm`` stub's,
    OpenAI's, a local model's — is dropped and rebuilt rather than appended to,
    because its vectors cannot be searched with this one's.

    :param python: The venv interpreter.
    :param skip: Leave Qdrant untouched.
    :param reset: Rebuild even when the stamp matches.
    """
    if skip:
        warn("--skip-ingest: leaving the Qdrant corpus as it is")
        return
    state, points, identity = corpus_state()
    if state == "current" and points and not reset:
        ok(f"corpus already present: {points} points embedded by {identity}")
        return
    if state == "stale":
        warn(f"'{COLLECTION}' was built by another embedder; rebuilding with {identity}")
    args = ["--reset"] if (reset or state == "stale") else []
    run([str(python), "-m", "scripts.ingest_regulatory_corpus", *args])
    ok(f"corpus embedded by {identity}")
