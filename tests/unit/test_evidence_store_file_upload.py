"""Tests for binary-safe EvidenceStore uploads."""
from __future__ import annotations

import base64
import hashlib

from aaa.platform.evidence import EvidenceStore


def test_store_file_round_trip_and_metadata_no_body_leak():
    store = EvidenceStore()
    data = b"hello upload"
    uri = store.store_file(
        "eng-upload", "customer_uploads", "risk_management_file_uri",
        "risk.txt", "text/plain", data, "test",
    )
    payload = store.get_artefact(uri)
    assert payload["sha256"] == hashlib.sha256(data).hexdigest()
    assert base64.b64decode(payload["body_base64"]) == data

    index = store.get_index("eng-upload")[0]
    assert index["bytes_size"] == len(data)
    assert index["filename"] == "risk.txt"
    assert "body_base64" not in index


def test_the_same_upload_is_indexed_once_across_reruns() -> None:
    """Streamlit reruns store every upload again; the index must not grow with them."""
    from aaa.platform.evidence import EvidenceStore

    store = EvidenceStore()
    first = [store.store_file("eng-idem", "customer_uploads", "technical_doc", "doc.txt",
                              "text/plain", b"same bytes", "streamlit") for _ in range(5)]
    changed = store.store_file("eng-idem", "customer_uploads", "technical_doc", "doc.txt",
                               "text/plain", b"edited bytes", "streamlit")
    assert len(set(first)) == 1 and changed != first[0]
    assert [e["uri"] for e in store.get_index("eng-idem")] == [first[0], changed]
