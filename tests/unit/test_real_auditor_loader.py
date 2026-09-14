"""Real-auditor behaviour: independent artefact loading from the store."""
from __future__ import annotations

import io

import pytest

from aaa.platform.artifact_loader import ArtifactUnavailable, infer_kind, load_artifact_from_uri
from aaa.platform.evidence import EvidenceStore


def _store_csv(store: EvidenceStore, eng: str) -> str:
    data = b"a,b,credit_risk\n1,x,1\n2,y,0\n"
    return store.store_file(eng, "customer_uploads", "evaluation_dataset_uri",
                            "eval.csv", "text/csv", data, "test")


def test_infer_kind():
    assert infer_kind("minio://e/p/model_v1.joblib") == "joblib"
    assert infer_kind("minio://e/p/eval.csv") == "csv"
    assert infer_kind("minio://e/p/doc.docx") == "docx"
    assert infer_kind("minio://e/p/blob.bin") == "bytes"


def test_loader_csv_roundtrip():
    store = EvidenceStore()
    uri = _store_csv(store, "eng-1")
    df = load_artifact_from_uri(uri, store, "csv")
    assert list(df.columns) == ["a", "b", "credit_risk"]
    assert len(df) == 2


def test_loader_joblib_roundtrip():
    joblib = pytest.importorskip("joblib")
    store = EvidenceStore()
    buf = io.BytesIO()
    joblib.dump({"hello": "world"}, buf)
    uri = store.store_file("eng-1", "customer_uploads", "model_artifact_uri",
                           "m.joblib", "application/octet-stream", buf.getvalue(), "test")
    assert load_artifact_from_uri(uri, store, "joblib") == {"hello": "world"}


def test_loader_missing_raises():
    store = EvidenceStore()
    with pytest.raises(ArtifactUnavailable):
        load_artifact_from_uri("minio://eng-1/customer_uploads/nope.csv", store, "csv")
    with pytest.raises(ArtifactUnavailable):
        load_artifact_from_uri(None, store, "csv")
