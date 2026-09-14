"""Post-ingest hybrid-retrieval coverage probes."""
from __future__ import annotations

import logging
from typing import Any

from scripts.ingest_regulatory_corpus.config import COVERAGE_PROBE_QUERIES
from scripts.ingest_regulatory_corpus.embed import dense_embed, sparse_embed

logger = logging.getLogger("ingest_regulatory_corpus")


def run_coverage_probes(client: Any, collection: str) -> None:
    """Warn when the newly-added standards cannot be retrieved from Qdrant.

    :param client: Qdrant client.
    :param collection: Corpus collection to probe.
    """
    from qdrant_client import models as qmodels

    dense_vectors = dense_embed(COVERAGE_PROBE_QUERIES)
    sparse_vectors = sparse_embed(COVERAGE_PROBE_QUERIES)
    for query, dense_vec, sparse_vec in zip(
            COVERAGE_PROBE_QUERIES, dense_vectors, sparse_vectors, strict=True):
        try:
            response = client.query_points(
                collection_name=collection,
                prefetch=[
                    qmodels.Prefetch(query=dense_vec, using="dense", limit=16),
                    qmodels.Prefetch(
                        query=qmodels.SparseVector(
                            indices=sparse_vec["indices"], values=sparse_vec["values"]),
                        using="sparse", limit=16),
                ],
                query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
                limit=3,
                with_payload=True,
            )
            if not response.points:
                logger.warning("coverage probe returned zero results: %s", query)
        except Exception as exc:  # pragma: no cover - operational warning only
            logger.warning("coverage probe failed for %r: %s", query, exc)
