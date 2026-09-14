"""OpenAI embedding provider.

Batched because the API caps request size; the batch is the historic
``client_doc_ingest`` value, kept so behaviour is unchanged when this provider
is selected (which it is by default).
"""
from __future__ import annotations

_MODEL = "text-embedding-3-large"
_DIM = 3072
_BATCH = 64


def _api_key() -> str:
    """Resolve the OpenAI key from the environment, then settings.

    Resolved here rather than borrowed from a tool module: the platform layer
    must not import from ``aaa.tools`` — doing so created a genuine import
    cycle (embeddings -> client_doc_ingest.config -> embeddings).

    :returns: The configured key, or an empty string.
    :rtype: str
    """
    import os

    from aaa.settings import settings

    return os.environ.get("OPENAI_API_KEY") or str(settings.openai_api_key)


class OpenAIEmbedder:
    """Embeds via OpenAI's embeddings endpoint."""

    def __init__(self, model: str = _MODEL, dim: int = _DIM) -> None:
        """Bind to *model*.

        :param model: OpenAI embedding model id.
        :type model: str
        :param dim: Vector width the model returns.
        :type dim: int
        """
        self.model_id = f"openai:{model}"
        self.dim = dim
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text, batching to respect request limits.

        :param texts: Input strings.
        :type texts: list[str]
        :returns: One vector per input, in order.
        :rtype: list[list[float]]
        """
        import openai

        client = openai.OpenAI(api_key=_api_key())
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH):
            resp = client.embeddings.create(
                model=self._model, input=texts[start:start + _BATCH]
            )
            vectors.extend([list(item.embedding) for item in resp.data])
        return vectors
