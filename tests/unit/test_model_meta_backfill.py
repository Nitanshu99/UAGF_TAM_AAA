"""Unit tests for the S6 model-meta backfill patch logic."""
from __future__ import annotations

from aaa.tools.model_meta.backfill import patch_stage_b


def test_fills_meta_and_promotes_data_dictionary() -> None:
    """Company meta is applied and data-dictionary values reach the top level."""
    stage_b = {"data_dictionary": {"target_column": "credit_risk", "positive_label": 1,
                                   "sensitive_feature_columns": ["age"]}}
    assert patch_stage_b(stage_b, "01_finclear_gmbh")
    assert stage_b["task_type"] == "binary_classification"
    assert stage_b["model_format"] == "joblib"
    assert stage_b["model_framework"] == "sklearn"
    assert stage_b["target_column"] == "credit_risk"
    assert stage_b["positive_label"] == 1
    assert stage_b["sensitive_feature_columns"] == ["age"]


def test_never_overwrites_existing_values() -> None:
    """Pre-set values survive the backfill untouched."""
    stage_b = {"task_type": "regression", "target_column": "y",
               "data_dictionary": {"target_column": "other"}}
    patch_stage_b(stage_b, "retailiq_ag")
    assert stage_b["task_type"] == "regression"
    assert stage_b["target_column"] == "y"


def test_idempotent_second_run_reports_no_change() -> None:
    """A second run on the same payload changes nothing."""
    stage_b = {"data_dictionary": {"target_column": "sales"}}
    assert patch_stage_b(stage_b, "02_retailiq_ag")
    assert not patch_stage_b(stage_b, "02_retailiq_ag")


def test_unknown_company_only_promotes_dictionary() -> None:
    """Unknown companies get no meta but still promote the data dictionary."""
    stage_b = {"data_dictionary": {"target_column": "y"}}
    assert patch_stage_b(stage_b, "unknown_co")
    assert stage_b["target_column"] == "y"
    assert "task_type" not in stage_b
