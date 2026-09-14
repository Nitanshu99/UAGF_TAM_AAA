"""A stamped corpus must reject a different model even at identical width."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from aaa.agents.tier1.regulatory_rag.provider_guard import (
    CorpusProviderMismatchError,
    assert_corpus_provider,
)

_OPENAI = "openai:text-embedding-3-large"


class _Client:
    """Qdrant double: a stamped identity plus a declared vector width."""

    def __init__(self, stamp: dict | None, width: int = 3072) -> None:
        self._stamp = stamp
        self._width = width

    def retrieve(self, collection_name, ids, with_payload):
        """Return the identity point, or nothing when the corpus is unstamped."""
        del collection_name, ids, with_payload
        if self._stamp is None:
            raise RuntimeError("meta collection does not exist")
        return [SimpleNamespace(payload=self._stamp)]

    def get_collection(self, collection_name):
        """Return a config declaring the dense-vector width."""
        del collection_name
        return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(
            vectors={"dense": SimpleNamespace(size=self._width)})))


def test_matching_stamp_passes():
    """The corpus and the configured embedder agree."""
    assert assert_corpus_provider(_Client({"model_id": _OPENAI}), "eu_ai_act") is None


def test_same_width_different_model_is_refused():
    """The gap the dimension check could not close: equal width, wrong model."""
    stamp = {"model_id": "local:some-3072-dim-model", "dim": 3072}
    with pytest.raises(CorpusProviderMismatchError) as excinfo:
        assert_corpus_provider(_Client(stamp, width=3072), "eu_ai_act")
    assert "some-3072-dim-model" in str(excinfo.value)
    assert _OPENAI in str(excinfo.value)


def test_unstamped_legacy_corpus_still_searches(caplog):
    """A missing stamp is not evidence of mismatch — warn, do not refuse."""
    assert assert_corpus_provider(_Client(None, width=3072), "eu_ai_act") is None
    assert "no embedding-model stamp" in caplog.text


def test_unstamped_corpus_with_wrong_width_is_still_refused():
    """The width fallback stays active for corpora that predate stamping."""
    with pytest.raises(CorpusProviderMismatchError):
        assert_corpus_provider(_Client(None, width=384), "eu_ai_act")


def test_mismatch_message_names_the_remedy():
    """Operators need the way out, not just the diagnosis."""
    with pytest.raises(CorpusProviderMismatchError) as excinfo:
        assert_corpus_provider(_Client({"model_id": "local:other"}), "eu_ai_act")
    assert "Re-ingest" in str(excinfo.value)
    assert "EMBEDDINGS_REGULATORY" in str(excinfo.value)
