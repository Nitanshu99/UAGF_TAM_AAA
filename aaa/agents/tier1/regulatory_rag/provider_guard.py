"""Regulatory-corpus binding of the shared embedding-provider guard.

The check itself lives in :mod:`aaa.platform.embeddings.guard`, shared with the
client-document store. This module only supplies the two things specific to the
corpus — the ``regulatory`` embedding purpose and the ``EMBEDDINGS_REGULATORY``
setting named in the error — so the two vector stores cannot drift apart.

``CorpusProviderMismatchError`` is retained as an alias so existing callers and
``except`` clauses keep working.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.embeddings.guard import ProviderMismatchError, assert_provider_matches

#: Historic name for :class:`ProviderMismatchError`.
CorpusProviderMismatchError = ProviderMismatchError

_SETTING = "EMBEDDINGS_REGULATORY"


def assert_corpus_provider(client: Any, collection: str) -> None:
    """Check the configured query embedder matches the regulatory *collection*.

    :param client: A Qdrant client.
    :type client: Any
    :param collection: Collection about to be searched.
    :type collection: str
    :raises ProviderMismatchError: If the corpus and query embedder differ.
    """
    assert_provider_matches(client, collection, "regulatory", _SETTING)
