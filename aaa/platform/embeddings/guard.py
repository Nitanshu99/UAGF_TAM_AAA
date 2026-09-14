"""Refuse to search a collection embedded by a different model.

Query vectors are only comparable to stored vectors from the same model. Two
checks, in order of authority: the recorded model identity is exact and catches
a *same-width* swap — the dangerous case, where Qdrant accepts the query and
the search returns confidently-ranked nonsense. Vector width is the fallback
for collections written before stamping existed.

Shared by every vector store in the repo rather than reimplemented per call
site: two copies of a check like this drift, and the one that drifts is the one
nobody was watching.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_VECTOR_NAME = "dense"


class ProviderMismatchError(RuntimeError):
    """Raised when a collection and the configured embedder disagree."""


def _declared_dim(client: Any, collection: str, vector_name: str) -> int | None:
    """Return *collection*'s declared vector width, or ``None`` if unreadable.

    :param client: A Qdrant client.
    :type client: Any
    :param collection: Collection name.
    :type collection: str
    :param vector_name: Named vector to inspect.
    :type vector_name: str
    :returns: Declared width, or ``None``.
    :rtype: int | None
    """
    try:
        params = client.get_collection(collection).config.params.vectors
        vector = params.get(vector_name) if isinstance(params, dict) else params
        return int(vector.size) if vector is not None else None
    except Exception:  # noqa: BLE001 — unreadable config must not block search
        return None


def assert_provider_matches(
    client: Any, collection: str, purpose: str, setting: str,
    vector_name: str = _DEFAULT_VECTOR_NAME,
) -> None:
    """Check the embedder configured for *purpose* matches *collection*.

    An unstamped collection is not evidence of a mismatch — it predates
    stamping — so it warns and falls back to the width check.

    :param client: A Qdrant client.
    :type client: Any
    :param collection: Collection about to be searched.
    :type collection: str
    :param purpose: Embedding purpose backing the query.
    :type purpose: str
    :param setting: Environment variable named in the error, for the operator.
    :type setting: str
    :param vector_name: Named vector to inspect.
    :type vector_name: str
    :raises ProviderMismatchError: If the collection and embedder differ.
    """
    from aaa.platform.embeddings import embedding_dim, embedding_identity
    from aaa.platform.embeddings.corpus_identity import read_identity

    configured = embedding_identity(purpose)
    # "Re-ingest" deliberately: both stores are populated by an *ingest* tool
    # (ingest_regulatory_corpus, client_doc_ingest) and USER_MANUAL Part 5 uses
    # the same word, so the message matches what the operator will look up.
    remedy = (f"Re-ingest {collection!r} with the current provider, or set "
              f"{setting} back to the one that built it.")

    stamp = read_identity(client, collection)
    if stamp and stamp.get("model_id"):
        if stamp["model_id"] != configured:
            raise ProviderMismatchError(
                f"collection {collection!r} was embedded with "
                f"{stamp['model_id']!r} but {setting} resolves to "
                f"{configured!r}. {remedy}")
        return

    declared = _declared_dim(client, collection, vector_name)
    if declared is None:
        return
    width = embedding_dim(purpose)
    if declared != width:
        raise ProviderMismatchError(
            f"collection {collection!r} holds {declared}-dimensional vectors but "
            f"{setting} resolves to {configured} ({width}-dimensional). {remedy}")
    logger.warning(
        "Collection %r carries no embedding-model stamp, so only vector width could "
        "be checked against %s. Two same-width models are indistinguishable here — "
        "re-ingest to record the model identity.", collection, configured,
    )
