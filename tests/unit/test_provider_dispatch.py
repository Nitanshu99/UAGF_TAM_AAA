"""Unit tests for the evidence-dispatch step that populates the landing zones."""
from __future__ import annotations

import httpx
import respx

from aaa.integrations.dispatch import apply_provider_evidence
from aaa.settings import AAASettings


def _cfg(**env: str) -> AAASettings:
    """Build settings from explicit values, ignoring the repo .env."""
    return AAASettings(_env_file=None, **env)  # pyright: ignore[reportCallIssue]


def _state(**overrides: object) -> dict:
    """Minimal post-phase state, gated in-scope for both S6 and S7 by default."""
    state = {"engagement_id": "eng-x", "risk_tier": "high",
             "client_submission": {"stage_b": {
                 "model_artifact_uri": "minio://x/model.joblib",
                 "task_type": "binary_classification",
                 "training_dataset_uri": "minio://x/train.csv"}},
             "phase_artefacts": {
                 "T10_explainability_report": {"uri": "minio://x/t10"},
                 "T11_robustness_report": {"uri": "minio://x/t11"}}}
    state.update(overrides)
    return state


def test_internal_mode_lands_artefact_refs() -> None:
    """Default mode packages internal artefact refs into both landing zones."""
    state = apply_provider_evidence(_state(), _cfg())
    assert state["xai_evidence_source"] == "internal"
    assert state["xai_evidence"]["explainability_report"] == {"uri": "minio://x/t10"}
    assert state["security_evidence"]["robustness_report"] == {"uri": "minio://x/t11"}


@respx.mock
def test_external_mode_lands_service_evidence() -> None:
    """External S6 evidence lands while S7 stays internal."""
    respx.post("http://s6.example/api/v1/evaluate").mock(
        return_value=httpx.Response(200, json={"shap": {"top": ["age"]}}))
    state = apply_provider_evidence(
        _state(), _cfg(S6_XAI_MODE="external", S6_XAI_BASE_URL="http://s6.example"))
    assert state["xai_evidence_source"] == "external"
    assert state["xai_evidence"]["shap"] == {"top": ["age"]}
    assert state["security_evidence_source"] == "internal"


@respx.mock
def test_external_failure_is_fail_soft() -> None:
    """A dead external service records an error stub instead of raising."""
    respx.post("http://s6.example/api/v1/evaluate").mock(
        return_value=httpx.Response(404))
    state = apply_provider_evidence(
        _state(), _cfg(S6_XAI_MODE="external", S6_XAI_BASE_URL="http://s6.example"))
    assert state["xai_evidence"]["error"] == "not_found"
    assert state["security_evidence_source"] == "internal"


def test_out_of_scope_engagement_lands_not_required_without_calling_a_provider() -> None:
    """A minimal-risk, non-agentic engagement never dispatches to a provider."""
    state = apply_provider_evidence(
        _state(risk_tier="minimal", client_submission={"stage_b": {}}), _cfg())
    assert state["xai_evidence_source"] == "not_required"
    assert "reason" in state["xai_evidence"]
    assert state["security_evidence_source"] == "not_required"
