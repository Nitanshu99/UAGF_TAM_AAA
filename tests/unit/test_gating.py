"""Unit tests for S6/S7 scope-derived gating (aaa.integrations.gating)."""
from __future__ import annotations

from aaa.integrations.gating import security_required, xai_required


def _state(risk_tier: str, is_llm_or_agentic: bool = False, **stage_b: object) -> dict:
    """Build a minimal audit state for gating decisions."""
    return {"risk_tier": risk_tier, "is_llm_or_agentic": is_llm_or_agentic,
            "client_submission": {"stage_b": stage_b}}


def test_high_risk_tabular_with_model_and_dataset_both_required():
    """A fully-evaluable high-risk model triggers both S6 and S7."""
    state = _state("high", model_artifact_uri="minio://x/model.joblib",
                   task_type="binary_classification", training_dataset_uri="minio://x/train.csv")
    assert xai_required(state)[0] is True
    assert security_required(state)[0] is True


def test_minimal_risk_doc_only_engagement_xai_not_required():
    """A minimal-risk, doc-only engagement does not require S6, with a reason."""
    state = _state("minimal")
    required, reason = xai_required(state)
    assert required is False
    assert "high risk tier" in reason


def test_llm_agentic_without_model_file_still_requires_security():
    """An LLM/agentic system with no model artefact still needs S7 (prompt-injection surface)."""
    state = _state("limited", is_llm_or_agentic=True)
    required, reason = security_required(state)
    assert required is True
    assert "agentic" in reason.lower()


def test_high_risk_without_model_artefact_xai_not_required():
    """High risk alone is not enough for S6 — an evaluable model is required."""
    state = _state("high")
    required, reason = xai_required(state)
    assert required is False
    assert "model artefact" in reason


def test_high_risk_model_without_task_type_xai_not_required():
    """A model artefact with no declared task_type cannot be evaluated by S6."""
    state = _state("high", model_artifact_uri="minio://x/model.joblib")
    required, reason = xai_required(state)
    assert required is False
    assert "task_type" in reason


def test_high_risk_model_without_dataset_xai_not_required():
    """A model with a task_type but no dataset cannot be run against real data."""
    state = _state("high", model_artifact_uri="minio://x/model.joblib",
                   task_type="binary_classification")
    required, reason = xai_required(state)
    assert required is False
    assert "dataset" in reason


def test_minimal_risk_non_agentic_security_not_required():
    """A minimal-risk, non-LLM/agentic system needs neither Art.13 nor Art.15 evidence."""
    state = _state("minimal", is_llm_or_agentic=False)
    required, _reason = security_required(state)
    assert required is False


def test_high_risk_always_requires_security_regardless_of_model():
    """Art. 15 is core for high risk even with no model artefact declared."""
    state = _state("high")
    assert security_required(state)[0] is True
