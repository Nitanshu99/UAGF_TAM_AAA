"""Unit tests for the F9 declaration corrections and the F7 layout backfill."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.platform.state.model_vocab import (
    ARTIFACT_KINDS,
    MODEL_FORMATS,
    MODEL_FRAMEWORKS,
    SUPERVISED_TASK_TYPES,
    TASK_TYPES,
)
from aaa.tools.model_meta.backfill import patch_stage_b
from aaa.tools.model_meta.corrections import correct_stage_b


def test_vocabularies_can_express_what_the_mock_cases_are() -> None:
    """The three values fix F9 established were unrepresentable now exist."""
    assert "anomaly_detection" in TASK_TYPES
    assert "chronos_sklearn_wrapper" in MODEL_FRAMEWORKS
    assert "huggingface_peft" in MODEL_FRAMEWORKS
    assert "huggingface_adapter" in MODEL_FORMATS
    assert ARTIFACT_KINDS == ("single_file", "directory")


def test_anomaly_detection_is_not_supervised() -> None:
    """An isolation forest is fitted unlabelled; S6 agrees (positive_label null)."""
    assert "anomaly_detection" not in SUPERVISED_TASK_TYPES


def test_correction_replaces_only_the_known_wrong_value() -> None:
    """A deliberate later edit is never clobbered."""
    stage_b = {"task_type": "binary_classification"}
    assert correct_stage_b(stage_b, "harbourlogistik_gmbh")
    assert stage_b["task_type"] == "anomaly_detection"

    deliberate = {"task_type": "multiclass_classification"}
    assert correct_stage_b(deliberate, "harbourlogistik_gmbh") == []
    assert deliberate["task_type"] == "multiclass_classification"


def test_correction_is_idempotent() -> None:
    """Re-running the backfill changes nothing."""
    stage_b = {"model_framework": "sklearn"}
    assert correct_stage_b(stage_b, "retailiq_ag")
    assert correct_stage_b(stage_b, "retailiq_ag") == []
    assert stage_b["model_framework"] == "chronos_sklearn_wrapper"


def test_unknown_company_is_left_alone() -> None:
    """The map is explicit; nothing is corrected by resemblance."""
    stage_b = {"task_type": "binary_classification"}
    assert correct_stage_b(stage_b, "someone_else_gmbh") == []


def test_layout_is_derived_from_the_uri_not_tabulated() -> None:
    """A case whose upload changes shape cannot keep a stale declaration."""
    stage_b = {"model_artifact_uri": "minio://eng/uploads/model_ab12_creditguard.joblib"}
    assert patch_stage_b(stage_b, "finclear_gmbh")
    assert stage_b["model_artifact_kind"] == "single_file"

    bundle = {"model_artifact_uri": "minio://eng/uploads/model_cd34_snapshot.zip"}
    patch_stage_b(bundle, "finclear_gmbh")
    assert bundle["model_artifact_kind"] == "directory"


def test_no_artefact_means_no_layout_claim() -> None:
    """LegalMind resolves a vendor model; there is no artefact to describe."""
    stage_b = {"model_access_mode": "base_plus_adapter", "model_artifact_uri": None}
    patch_stage_b(stage_b, "legalmind_ai_ltd")
    assert stage_b.get("model_artifact_kind") is None


def test_immutable_columns_come_from_the_stated_source_only() -> None:
    """The S6 sheet gives FinClear's set verbatim; nothing else is guessed."""
    finclear: dict = {}
    patch_stage_b(finclear, "finclear_gmbh")
    assert finclear["immutable_feature_columns"] == ["age", "credit_history"]

    other: dict = {}
    patch_stage_b(other, "talentsift_gmbh")
    assert other.get("immutable_feature_columns") is None


@pytest.mark.parametrize("path,field,expected", [
    ("mock/02_retailiq_ag/stage_b.json", "model_framework", "chronos_sklearn_wrapper"),
    ("mock/03_harbourlogistik_gmbh/stage_b.json", "task_type", "anomaly_detection"),
    ("mock/04_legalmindd_ai_ltd/stage_b.json", "model_format", "huggingface_adapter"),
    ("mock/04_legalmindd_ai_ltd/stage_b.json", "model_framework", "huggingface_peft"),
])
def test_fixtures_now_declare_what_their_model_type_says(path, field, expected) -> None:
    """Each corrected declaration agrees with the case's own ``model_type``."""
    stage_b = json.loads(Path(path).read_text(encoding="utf-8"))
    assert stage_b[field] == expected
