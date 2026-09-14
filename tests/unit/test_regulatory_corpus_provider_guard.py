"""A corpus embedded by one model must not be queried by another."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from aaa.agents.tier1.regulatory_rag.provider_guard import (
    CorpusProviderMismatchError,
    assert_corpus_provider,
)


def _client(width: int):
    """A Qdrant double whose collection declares *width*-dimensional vectors."""
    vector = SimpleNamespace(size=width)
    return SimpleNamespace(get_collection=lambda name: SimpleNamespace(
        config=SimpleNamespace(params=SimpleNamespace(vectors={"dense": vector}))))


def test_matching_width_passes():
    """The default OpenAI provider matches a 3072-dim corpus."""
    assert assert_corpus_provider(_client(3072), "eu_ai_act") is None


def test_mismatched_width_is_refused():
    """A 384-dim corpus under a 3072-dim query embedder must not be searched."""
    with pytest.raises(CorpusProviderMismatchError):
        assert_corpus_provider(_client(384), "eu_ai_act")


def test_mismatch_message_names_both_sides_and_the_remedy():
    """The error has to be actionable, not just a dimension complaint."""
    with pytest.raises(CorpusProviderMismatchError) as excinfo:
        assert_corpus_provider(_client(768), "eu_ai_act")
    message = str(excinfo.value)
    assert "768" in message and "3072" in message
    assert "EMBEDDINGS_REGULATORY" in message and "Re-ingest" in message


def test_unreadable_collection_does_not_block_search():
    """A guard that cannot read the config must not become an outage."""
    broken = SimpleNamespace(
        get_collection=lambda name: (_ for _ in ()).throw(RuntimeError("qdrant down")))
    assert assert_corpus_provider(broken, "eu_ai_act") is None
