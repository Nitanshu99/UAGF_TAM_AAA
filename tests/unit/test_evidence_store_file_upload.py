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
