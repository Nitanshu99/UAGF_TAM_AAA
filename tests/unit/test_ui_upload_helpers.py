"""Tests for Streamlit upload helper behavior without launching a browser."""
from __future__ import annotations

from aaa.platform.evidence import EvidenceStore
from aaa.ui.app import _store_uploaded_file


class _FakeUpload:
    name = "model.json"
    type = "application/json"

    @staticmethod
    def getvalue() -> bytes:
        return b'{"model": "demo"}'


def test_store_uploaded_file_returns_uri_for_stage_b_payload():
    store = EvidenceStore()
    uri = _store_uploaded_file(store, "eng-ui", "model_metadata_uri", _FakeUpload())
    assert uri and uri.startswith("minio://eng-ui/customer_uploads/model_metadata_uri")
    assert store.get_artefact(uri)["filename"] == "model.json"
