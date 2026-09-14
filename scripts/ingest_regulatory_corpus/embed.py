"""Dense (configured provider) and sparse (BM25) embedding (Steps 3 + 4)."""
from __future__ import annotations

from scripts.ingest_regulatory_corpus.config import SPARSE_MODEL
from scripts.ingest_regulatory_corpus.deps import require


def dense_embed(texts: list[str]) -> list[list[float]]:
    """Embed *texts* with the provider configured for the ``regulatory`` purpose.

    Routed through :mod:`aaa.platform.embeddings` rather than a direct OpenAI
    client, so the corpus is written by the same embedder that will query it:
    ``EMBEDDINGS_REGULATORY`` chooses ``openai``, ``openrouter`` or ``local``,
    and the collection width (:func:`~.config.dense_dim`) and identity stamp
    come from that one choice. A direct client here embedded with OpenAI no
    matter what the setting said, so any other provider produced a corpus the
    searcher could never match.

    :param texts: Texts to embed.
    :returns: One dense vector per text.
    """
    from aaa.platform.embeddings import embed_texts

    return embed_texts(texts, "regulatory")


def sparse_embed(texts: list[str]) -> list[dict[str, list]]:
    """Embed *texts* with fastembed BM25.

    :param texts: Texts to embed.
    :returns: ``[{indices: [...], values: [...]}, ...]`` sparse vectors.
    """
    fe = require("fastembed")
    encoder = fe.SparseTextEmbedding(model_name=SPARSE_MODEL)
    out: list[dict[str, list]] = []
    for emb in encoder.embed(texts):
        out.append({"indices": emb.indices.tolist(), "values": emb.values.tolist()})
    return out
