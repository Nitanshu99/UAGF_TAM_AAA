"""Streamlit upload / version-normalisation helpers (no browser launched)."""
from __future__ import annotations

from aaa.platform.evidence import EvidenceStore
from aaa.ui.app import _normalise_version, _store_uploaded_file


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


def test_normalise_version_strips_common_v_prefix():
    assert _normalise_version("v2.1") == "2.1"
    assert _normalise_version(" V2.1.0 ") == "2.1.0"
    assert _normalise_version("release-2.1") == "release-2.1"
