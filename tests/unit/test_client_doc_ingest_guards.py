"""client_doc_ingest: credential guards and error wrapping."""
from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from aaa.tools import client_doc_ingest

_config = importlib.import_module("aaa.tools.client_doc_ingest.config")
_core = importlib.import_module("aaa.tools.client_doc_ingest.core")
_EMPTY = {"collection_name": "client_docs_test_eng_001", "chunks_indexed": 0,
          "sources": []}


def test_ingest_without_openai_key_is_safe_noop(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(_config, "settings", SimpleNamespace(openai_api_key=""))

    def _unexpected_qdrant_client():
        raise AssertionError("Qdrant client should not be created without OPENAI_API_KEY")

    monkeypatch.setattr(_core, "_qdrant_client", _unexpected_qdrant_client)
    result = client_doc_ingest.client_doc_ingest("test-eng-001", ["minio://eng/doc.txt"])
    assert result == _EMPTY


def test_embeddings_available_uses_settings_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(_config, "settings", SimpleNamespace(openai_api_key="test-key"))
    assert client_doc_ingest._embeddings_available() is True


def test_ingest_wraps_unexpected_errors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(_core, "_embeddings_available", lambda: True)

    def _boom():
        raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr(_core, "_qdrant_client", _boom)
    with pytest.raises(client_doc_ingest.ClientDocIngestError, match="qdrant unavailable"):
        client_doc_ingest.client_doc_ingest("test-eng-001", ["minio://eng/doc.txt"])
