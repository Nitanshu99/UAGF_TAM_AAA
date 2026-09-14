"""client_doc_ingest: safe dry-run, search, and chunk traceability."""
from __future__ import annotations

import importlib

from aaa.tools import client_doc_ingest

_EMPTY = {"collection_name": "client_docs_test_eng_001", "chunks_indexed": 0,
          "sources": []}


def test_empty_ingest_is_safe_dry_run():
    assert client_doc_ingest.client_doc_ingest("test-eng-001", []) == _EMPTY


def test_search_without_collection_returns_list():
    results = client_doc_ingest.client_doc_search("test-eng-001", "risk management")
    assert isinstance(results, list)


def test_text_chunk_metadata_is_traceable():
    chunking = importlib.import_module("aaa.tools.client_doc_ingest.chunking")
    chunks = chunking._chunks_for_document(
        "minio://eng/stage_b/risk_management_file.txt",
        b"# Risk Management\n" + (b"control evidence " * 200))
    assert chunks
    assert chunks[0]["source_uri"] == "minio://eng/stage_b/risk_management_file.txt"
    assert chunks[0]["document_role"] == "risk_management_file"
    assert chunks[0]["content_type"] == "txt"
    assert chunks[0]["source_sha256"]
    assert chunks[0]["chunk_total"] == len(chunks)


def test_chunks_keep_their_line_breaks_and_headings() -> None:
    """Every whitespace run became one space, so tables flattened and no heading was ever found."""
    from aaa.tools.client_doc_ingest.chunking import _chunks_for_document, normalise_layout

    text = ("2. Monitored signals\nSignal   Source   Status\n\n\nLatency p95  Service telemetry  Live\n"
            "Feature drift  Live traffic  To\nbuild\n")
    assert normalise_layout(text).splitlines() == [
        "2. Monitored signals", "Signal Source Status", "Latency p95 Service telemetry Live",
        "Feature drift Live traffic To", "build"]
    chunk = _chunks_for_document("minio://e/customer_uploads/plan.txt", text.encode("utf-8"))[0]
    assert "\n" in chunk["text"] and chunk["section_hint"] == "2. Monitored signals"
