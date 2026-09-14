"""Local sentence-transformers provider — nothing leaves the host.

The model id is deliberately not defaulted. Picking one silently would fix a
retrieval-quality and download-size trade-off on the operator's behalf, and
would let a vector store be built against a model nobody chose.
"""
from __future__ import annotations

from aaa.platform.embeddings.base import EmbeddingConfigError


class LocalEmbedder:
    """Embeds in-process with a sentence-transformers model."""

    def __init__(self, model_id: str) -> None:
        """Load *model_id* and read its true output width.

        :param model_id: A sentence-transformers model identifier.
        :type model_id: str
        :raises EmbeddingConfigError: If *model_id* is blank or unloadable.
        """
        if not model_id:
            raise EmbeddingConfigError(
                "EMBEDDINGS_LOCAL_MODEL is unset. Selecting a 'local' embedding "
                "provider requires naming the sentence-transformers model to use "
                "(for example all-MiniLM-L6-v2 or all-mpnet-base-v2)."
            )
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_id)
        except Exception as exc:
            raise EmbeddingConfigError(
                f"local embedding model {model_id!r} could not be loaded "
                f"({type(exc).__name__}: {exc})"
            ) from exc
        self.model_id = f"local:{model_id}"
        self.dim = int(self._model.get_sentence_embedding_dimension() or 0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text, computed locally.

        :param texts: Input strings.
        :type texts: list[str]
        :returns: One vector per input, in order.
        :rtype: list[list[float]]
        """
        vectors = self._model.encode(list(texts), convert_to_numpy=True)
        return [[float(v) for v in row] for row in vectors]
