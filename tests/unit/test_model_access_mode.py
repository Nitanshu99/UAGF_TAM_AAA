"""Mode-aware validation of the Stage B access-mode rules."""
from __future__ import annotations

from typing import Any

from aaa.tools.annex_iv_validator.checks.model_meta import check_model_meta
from aaa.tools.annex_iv_validator.validationresult import ValidationResult


def gaps_for(dossier: dict[str, Any]) -> list[str]:
    """Return the fields the checks report as defective for *dossier*."""
    result = ValidationResult(is_valid=True)
    check_model_meta(result, dossier)
    return [c.field for c in result.missing_conditional if c.applicable and not c.present]


def test_format_without_artefact_or_reference_is_flagged() -> None:
    """The case-04 defect: a format claim with nothing behind it.

    The old gate keyed on ``bool(model_artifact_uri)``, so this dossier had
    every check marked not-applicable and passed intake in silence while S6
    hunted for weights that were never going to exist.
    """
    gaps = gaps_for({"model_format": "huggingface", "model_framework": "transformers",
                     "task_type": "llm_generation"})
    assert "model_format" in gaps
    assert "model_framework" in gaps


def test_hosted_api_rejects_a_serialisation_format() -> None:
    """A hosted model has no artefact, so a format describes nothing."""
    gaps = gaps_for({"model_access_mode": "hosted_api", "model_format": "huggingface",
                     "model_reference": {"provider": "openai", "model_id": "gpt-4o-2024-08-06",
                                         "revision": "2024-08-06", "auth_type": "api_key"}})
    assert "model_format" in gaps


def test_artifact_upload_is_unaffected() -> None:
    """The four uploaded-artefact mock cases must keep passing cleanly."""
    assert gaps_for({"model_access_mode": "artifact_upload", "task_type": "binary_classification",
                     "model_artifact_uri": "minio://x/model.joblib", "model_format": "joblib",
                     "target_column": "y", "positive_label": 1}) == []


def test_legacy_dossier_without_a_mode_keeps_its_old_checks() -> None:
    """An uploaded artefact with no declared mode is still an artifact upload.

    The mode itself is requested — dossiers should migrate — but the artefact
    checks must not silently stop applying the way they used to.
    """
    gaps = gaps_for({"model_artifact_uri": "minio://x/model.joblib",
                     "model_format": "joblib", "task_type": "regression"})
    assert gaps == ["model_access_mode"]
