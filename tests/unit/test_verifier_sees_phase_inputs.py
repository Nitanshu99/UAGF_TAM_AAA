"""The Verifier may link an artefact to the model and data it was computed from (T-20260913-076)."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.sources import review_evidence_uris


def test_declared_inputs_follow_the_dispatch_uris_once_each() -> None:
    dispatch = {"evidence_uris": ["minio://e/T01b.json", "minio://e/model.pkl"],
                "declaration_summary": {"model_artifact_uri": "minio://e/model.pkl",
                                        "stage_b": {"evaluation_dataset_uri": "minio://e/eval.csv",
                                                    "training_dataset_uri": None}}}
    assert review_evidence_uris(dispatch) == [
        "minio://e/T01b.json", "minio://e/model.pkl", "minio://e/eval.csv"]


def test_a_dispatch_without_inputs_is_unchanged() -> None:
    assert review_evidence_uris({"evidence_uris": ["minio://e/T01a.json"]}) == ["minio://e/T01a.json"]
