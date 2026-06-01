"""Tests for per-engagement client-document ingestion helpers."""
from __future__ import annotations

from aaa.tools import client_doc_ingest


def test_empty_ingest_is_safe_dry_run():
    result = client_doc_ingest.client_doc_ingest("test-eng-001", [])
    assert result == {
        "collection_name": "client_docs_test_eng_001",
        "chunks_indexed": 0,
        "sources": [],
    }


def test_search_without_collection_returns_list():
    results = client_doc_ingest.client_doc_search("test-eng-001", "risk management")
    assert isinstance(results, list)


def test_text_chunk_metadata_is_traceable():
    chunks = client_doc_ingest._chunks_for_document(
        "minio://eng/stage_b/risk_management_file.txt",
        b"# Risk Management\n" + (b"control evidence " * 200),
    )
    assert chunks
    assert chunks[0]["source_uri"] == "minio://eng/stage_b/risk_management_file.txt"
    assert chunks[0]["document_role"] == "risk_management_file"
    assert chunks[0]["content_type"] == "txt"
    assert chunks[0]["source_sha256"]
    assert chunks[0]["chunk_total"] == len(chunks)
