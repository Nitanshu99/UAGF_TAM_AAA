"""OpenRouter embedding provider — OpenAI's model, reached with the OpenRouter key.

OpenRouter fronts ``openai/text-embedding-3-large`` on an OpenAI-compatible
``/embeddings`` endpoint. A deployment that already routes its agent roster
through OpenRouter (``PROVIDER=openrouter``) therefore needs no second vendor
key for retrieval: the vectors come from the same model at the same 3072
width, and only the key and the gateway differ.

The gateway is part of the recorded identity. ``OPENROUTER_API_BASE`` — the
name LiteLLM reads for the chat path — can point this provider at another
OpenAI-compatible host (a proxy, or the bootstrap's no-spend stub), and a corpus
embedded through one gateway must not be searched through another as if the
vectors were interchangeable.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

from aaa.platform.embeddings.base import EmbeddingConfigError

#: OpenRouter's slug for OpenAI's large embedding model.
MODEL = "openai/text-embedding-3-large"
_DIM = 3072
_BATCH = 64
#: The public gateway. ``OPENROUTER_API_BASE`` overrides it, for LiteLLM too.
DEFAULT_API_BASE = "https://openrouter.ai/api/v1"


def api_base() -> str:
    """Return the OpenRouter API root this process would call (no trailing slash)."""
    return (os.environ.get("OPENROUTER_API_BASE") or DEFAULT_API_BASE).rstrip("/")


def api_key() -> str:
    """Resolve the OpenRouter key from the environment, then settings."""
    from aaa.settings import settings

    return os.environ.get("OPENROUTER_API_KEY") or str(settings.openrouter_api_key)


def gateway_tag(base: str) -> str:
    """``openrouter`` for the public gateway, ``openrouter@<host>`` for any other."""
    if base.rstrip("/") == DEFAULT_API_BASE:
        return "openrouter"
    return f"openrouter@{urlparse(base).netloc or base}"


class OpenRouterEmbedder:
    """Embeds via OpenRouter's OpenAI-compatible embeddings endpoint."""

    def __init__(self, model: str = MODEL, dim: int = _DIM) -> None:
        """Bind to *model* on the configured gateway.

        :param model: OpenRouter embedding model slug.
        :param dim: Vector width the model returns.
        """
        self._model = model
        self.dim = dim
        self._base = api_base()
        self.model_id = f"{gateway_tag(self._base)}:{model}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text, batching to respect request limits.

        :param texts: Input strings.
        :returns: One vector per input, in order.
        :raises EmbeddingConfigError: When no OpenRouter key is configured.
        """
        import openai

        key = api_key()
        if not key:
            raise EmbeddingConfigError(
                "OPENROUTER_API_KEY is unset: the 'openrouter' embedding provider "
                "sends every request with it.")
        client = openai.OpenAI(api_key=key, base_url=self._base)
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH):
            resp = client.embeddings.create(model=self._model, input=texts[start:start + _BATCH])
            vectors.extend([list(item.embedding) for item in resp.data])
        return vectors
