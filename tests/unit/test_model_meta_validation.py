"""Unit tests for the S6 model-meta conditional checks in annex_iv_validator."""
from __future__ import annotations

import json
from pathlib import Path

from aaa.tools.annex_iv_validator import annex_iv_validator

_FIXTURE = Path("mock/01_finclear_gmbh/stage_b.json")


def _dossier(**overrides: object) -> dict:
    """Load the finclear Stage B fixture with *overrides* applied."""
    dossier = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    dossier.update(overrides)
    return dossier


def _by_field(result: object, name: str) -> list:
    """Return the conditional statuses recorded for *name*."""
    return [c for c in result.missing_conditional if c.field == name]  # type: ignore[attr-defined]


def test_missing_task_type_with_model_yields_finding_not_crash() -> None:
    """A model upload without task_type is flagged but intake stays valid."""
    result = annex_iv_validator(_dossier(model_artifact_uri="minio://x/model.joblib",
                                         task_type=None),
                                "tabular")
    status = _by_field(result, "task_type")[0]
    assert status.applicable and not status.present
    assert result.is_valid  # finding, not a hard failure


def test_compliant_payload_has_all_statuses_present() -> None:
    """A fully-populated dossier records every applicable status as present."""
    result = annex_iv_validator(_dossier(
        model_artifact_uri="minio://x/model.joblib",
        training_dataset_uri="minio://x/train.csv",
        task_type="binary_classification", model_format="joblib",
        model_framework="sklearn", target_column="credit_risk",
        positive_label=1, sensitive_feature_columns=["age_group"]), "tabular")
    assert result.is_valid
    for name in ("task_type", "model_format", "target_column", "positive_label"):
        status = _by_field(result, name)[0]
        assert status.applicable and status.present, name


def test_no_model_at_all_makes_meta_not_applicable() -> None:
    """A dossier offering no model in any form records the S6 fields as N/A."""
    result = annex_iv_validator(
        _dossier(model_format=None, model_framework=None, task_type=None,
                 model_access_mode=None), "tabular")
    assert not _by_field(result, "task_type")[0].applicable
    assert not _by_field(result, "model_format")[0].applicable


def test_format_declared_with_nothing_behind_it_is_flagged() -> None:
    """A format claim backed by no artefact and no reference is a finding.

    This is the case-04 defect: the dossier declared ``huggingface`` /
    ``transformers`` with no ``model_artifact_uri`` anywhere, and the old
    ``bool(model_artifact_uri)`` gate marked every check not-applicable, so
    intake passed in silence while S6 hunted for weights that never existed.
    """
    result = annex_iv_validator(_dossier(
        model_format="huggingface", model_framework="transformers",
        task_type="llm_generation", model_artifact_uri=None,
        model_access_mode=None), "tabular")
    for name in ("model_format", "model_framework"):
        status = _by_field(result, name)[0]
        assert status.applicable and not status.present, name
    assert result.is_valid  # a finding, never a hard intake failure
