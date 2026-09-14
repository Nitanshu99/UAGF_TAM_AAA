"""Batch embedding for client-document chunks.

Routed through :mod:`aaa.platform.embeddings` under the ``client_docs``
purpose. This is the path that embeds the customer's own compliance
documentation, so it is the one most likely to be configured local.
"""
from __future__ import annotations

from aaa.platform.embeddings import embed_texts


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed *texts* with the provider configured for client documents.

    :param texts: Chunk texts to embed.
    :type texts: list[str]
    :returns: One vector per chunk, in order.
    :rtype: list[list[float]]
    """
    return embed_texts(texts, "client_docs")
