"""Text embedding behind one seam, configurable per purpose.

Three call sites embed text — the customer's compliance dossier
(``client_docs``), regulatory-corpus queries (``regulatory``) and dense
evidence re-ranking (``evidence``) — and each chooses its provider
independently. That split exists so confidential client documentation can be
embedded on-host while public EU legal text keeps a hosted model's retrieval
quality; forcing one choice on all three would trade one against the other.

Callers ask for :func:`embedding_dim` rather than assuming a width, because
providers differ (3072 for OpenAI's large model, 384 or 768 for typical
sentence-transformers) and a vector store built against the wrong number fails
at upsert or, worse, mis-ranks silently.

Three providers: ``openai`` (the default), ``openrouter`` (the same OpenAI
model through OpenRouter's gateway, so one key covers agents and retrieval) and
``local`` (sentence-transformers, nothing leaves the host).
"""
from aaa.platform.embeddings.base import Embedder, EmbeddingConfigError  # noqa: F401
from aaa.platform.embeddings.credentials import (  # noqa: F401
    credentials_present,
    missing_credential,
)
from aaa.platform.embeddings.select import (  # noqa: F401
    PURPOSES,
    get_embedder,
    provider_for,
    reset_cache,
)


def embed_texts(texts: list[str], purpose: str) -> list[list[float]]:
    """Embed *texts* with the provider configured for *purpose*.

    :param texts: Input strings.
    :type texts: list[str]
    :param purpose: One of :data:`PURPOSES`.
    :type purpose: str
    :returns: One vector per input, in order.
    :rtype: list[list[float]]
    """
    return get_embedder(purpose).embed(texts)


def embedding_dim(purpose: str) -> int:
    """Return the vector width the provider for *purpose* produces.

    :param purpose: One of :data:`PURPOSES`.
    :type purpose: str
    :returns: Vector dimensionality.
    :rtype: int
    """
    return get_embedder(purpose).dim


def embedding_identity(purpose: str) -> str:
    """Return the provider/model identity recorded alongside stored vectors.

    :param purpose: One of :data:`PURPOSES`.
    :type purpose: str
    :returns: An identity such as ``openai:text-embedding-3-large``.
    :rtype: str
    """
    return get_embedder(purpose).model_id


__all__ = [
    "Embedder", "EmbeddingConfigError", "PURPOSES", "credentials_present",
    "embed_texts", "embedding_dim", "embedding_identity", "get_embedder",
    "missing_credential", "provider_for", "reset_cache",
]
