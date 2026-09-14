"""The contract every embedding provider satisfies.

``dim`` is an attribute rather than something callers hardcode: OpenAI's
``text-embedding-3-large`` is 3072-dimensional and typical sentence-transformers
models are 384 or 768, so any vector store built against a constant breaks the
moment the provider changes.
"""
from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    """A text-to-vector provider."""

    #: Width of the vectors this provider returns.
    dim: int

    #: Human-readable identity, recorded so a store can detect a later swap.
    model_id: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in order."""
        raise NotImplementedError


class EmbeddingConfigError(RuntimeError):
    """Raised when embedding configuration is unusable."""
