"""Resolve which provider serves each embedding purpose.

Each purpose is configured independently so the confidential client dossier can
stay on-host while the public regulatory corpus keeps a hosted model's retrieval
quality. Providers are cached per purpose — constructing a
sentence-transformers model per call would dominate ingest time.
"""
from __future__ import annotations

from aaa.platform.embeddings.base import Embedder, EmbeddingConfigError

#: Configured embedding purposes → the settings field naming their provider.
PURPOSES: dict[str, str] = {
    "client_docs": "embeddings_client_docs",
    "regulatory": "embeddings_regulatory",
    "evidence": "embeddings_evidence",
}

_CACHE: dict[str, Embedder] = {}


def provider_for(purpose: str) -> str:
    """Return the provider name configured for *purpose*.

    :param purpose: One of :data:`PURPOSES`.
    :type purpose: str
    :returns: ``"openai"``, ``"openrouter"`` or ``"local"``.
    :rtype: str
    :raises EmbeddingConfigError: If *purpose* is not a known purpose.
    """
    from aaa.settings import settings

    if purpose not in PURPOSES:
        raise EmbeddingConfigError(
            f"unknown embedding purpose {purpose!r}; expected one of {sorted(PURPOSES)}"
        )
    return str(getattr(settings, PURPOSES[purpose])).strip().lower()


def get_embedder(purpose: str) -> Embedder:
    """Return the cached provider serving *purpose*.

    :param purpose: One of :data:`PURPOSES`.
    :type purpose: str
    :returns: The configured provider.
    :rtype: Embedder
    :raises EmbeddingConfigError: On an unknown purpose or provider name.
    """
    if purpose in _CACHE:
        return _CACHE[purpose]
    name = provider_for(purpose)
    if name == "local":
        from aaa.platform.embeddings.local import LocalEmbedder
        from aaa.settings import settings

        embedder: Embedder = LocalEmbedder(str(settings.embeddings_local_model).strip())
    elif name == "openai":
        from aaa.platform.embeddings.openai import OpenAIEmbedder

        embedder = OpenAIEmbedder()
    elif name == "openrouter":
        from aaa.platform.embeddings.openrouter import OpenRouterEmbedder

        embedder = OpenRouterEmbedder()
    else:
        raise EmbeddingConfigError(
            f"unknown embedding provider {name!r} for purpose {purpose!r}; "
            f"expected 'openai', 'openrouter' or 'local'"
        )
    _CACHE[purpose] = embedder
    return embedder


def reset_cache() -> None:
    """Drop cached providers — test-only helper."""
    _CACHE.clear()
