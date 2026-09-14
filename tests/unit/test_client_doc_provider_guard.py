"""Client-document search must refuse a collection built by another model.

Uploads are indexed once per engagement and reused, so changing
``EMBEDDINGS_CLIENT_DOCS`` mid-engagement would otherwise match new query
vectors against old ones — against the customer's own dossier, which is the
evidence an audit conclusion rests on.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from aaa.platform.embeddings.guard import ProviderMismatchError, assert_provider_matches
from aaa.tools.client_doc_ingest import search as search_mod

_SETTING = "EMBEDDINGS_CLIENT_DOCS"
_OPENAI = "openai:text-embedding-3-large"


class _Client:
    """Qdrant double carrying an optional identity stamp and a vector width."""

    def __init__(self, stamp: dict | None, width: int = 3072) -> None:
        self._stamp, self._width = stamp, width

    def retrieve(self, collection_name, ids, with_payload):
        """Return the stamp point, or raise when the collection is unstamped."""
        del collection_name, ids, with_payload
        if self._stamp is None:
            raise RuntimeError("meta collection absent")
        return [SimpleNamespace(payload=self._stamp)]

    def get_collection(self, collection_name):
        """Declare the dense-vector width."""
        del collection_name
        return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(
            vectors={"dense": SimpleNamespace(size=self._width)})))


def test_same_width_different_model_is_refused():
    """Equal width, different model — invisible to a dimensionality check."""
    stamp = {"model_id": "local:pretend-3072", "dim": 3072}
    with pytest.raises(ProviderMismatchError) as excinfo:
        assert_provider_matches(_Client(stamp), "client_docs_eng_1",
                                "client_docs", _SETTING)
    assert _SETTING in str(excinfo.value)
    assert "Re-ingest" in str(excinfo.value)


def test_matching_model_passes():
    """The engagement was indexed by the configured embedder."""
    assert assert_provider_matches(
        _Client({"model_id": _OPENAI}), "client_docs_eng_1",
        "client_docs", _SETTING) is None


def test_search_returns_no_hits_on_mismatch(monkeypatch, caplog):
    """A mismatch yields no evidence rather than wrongly-ranked evidence."""
    monkeypatch.setattr(search_mod, "_embeddings_available", lambda: True)
    monkeypatch.setattr(search_mod, "_qdrant_client",
                        lambda: _Client({"model_id": "local:other"}))
    monkeypatch.setattr(search_mod, "_collection_exists", lambda c, n: True)
    monkeypatch.setattr(search_mod, "_embed",
                        lambda t: pytest.fail("embedded despite a refused search"))

    assert search_mod.client_doc_search("eng-1", "data governance") == []


def test_mismatch_is_logged_at_error_not_warning(monkeypatch, caplog):
    """Operators must be able to tell a config fault from an empty dossier."""
    import logging
    monkeypatch.setattr(search_mod, "_embeddings_available", lambda: True)
    monkeypatch.setattr(search_mod, "_qdrant_client",
                        lambda: _Client({"model_id": "local:other"}))
    monkeypatch.setattr(search_mod, "_collection_exists", lambda c, n: True)

    with caplog.at_level(logging.ERROR):
        search_mod.client_doc_search("eng-1", "q")

    assert any(r.levelno == logging.ERROR and "refused" in r.message
               for r in caplog.records)
