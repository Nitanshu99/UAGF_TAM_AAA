"""Rules over the ``model_reference`` block and the S6 hand-off warnings."""
from __future__ import annotations

from typing import Any

import pytest

from aaa.integrations.handoff import build_handoff
from tests.unit.test_model_access_mode import gaps_for


def _reference(**overrides: Any) -> dict[str, Any]:
    """A complete huggingface adapter reference, with *overrides* applied."""
    reference = {
        "provider": "huggingface",
        "model_id": "cimphony-ai-admin/Cimphony-Mistral-Law-7B",
        "revision": "c7cc200adeab6197b17e3bf6cdf4bc11f79bb684",
        "base_model_id": "mistralai/Mistral-7B-v0.1",
        "base_model_revision": "27d67f1b5f57dc0953326b2601d68371d40ea8da",
        "peft_type": "LORA",
        "adapter_reference": "cimphony-ai-admin/Cimphony-Mistral-Law-7B",
    }
    reference.update(overrides)
    return reference


def test_mutable_revision_is_not_a_pin() -> None:
    """A branch name re-points, so it cannot identify the audited weights."""
    gaps = gaps_for({"model_access_mode": "registry_reference", "model_format": "safetensors",
                     "model_reference": {"provider": "huggingface", "model_id": "org/model",
                                         "revision": "main", "gated": False,
                                         "license": "apache-2.0"}})
    assert "model_reference.revision" in gaps


def test_complete_adapter_reference_is_clean() -> None:
    """The repointed case 04 satisfies every base_plus_adapter rule."""
    assert gaps_for({"model_access_mode": "base_plus_adapter", "model_format": "safetensors",
                     "task_type": "llm_generation", "model_reference": _reference()}) == []


@pytest.mark.parametrize("sources,accepted", [
    ({}, False),
    ({"adapter_uri": "minio://x/adapter.safetensors"}, True),
    ({"adapter_reference": "org/adapter"}, True),
    ({"adapter_uri": "minio://x/a.safetensors", "adapter_reference": "org/adapter"}, False),
])
def test_adapter_needs_exactly_one_source(sources: dict[str, Any], accepted: bool) -> None:
    """Neither zero nor two adapter sources leave S6 a single thing to load."""
    reference = _reference()
    reference.pop("adapter_reference")
    reference.update(sources)
    gaps = gaps_for({"model_access_mode": "base_plus_adapter", "model_format": "safetensors",
                     "model_reference": reference})
    assert ("model_reference.adapter_uri|adapter_reference" not in gaps) is accepted


def test_handoff_warns_on_an_unresolvable_reference() -> None:
    """S6 cannot fetch a vendor model without provider, model_id and revision."""
    _payload, warnings = build_handoff({"engagement_id": "e", "client_submission": {
        "stage_b": {"model_access_mode": "hosted_api"}}})
    assert len(warnings) == 3
    assert all("model_reference" in warning for warning in warnings)


def test_handoff_is_quiet_when_the_reference_resolves() -> None:
    """A fully identified hosted model needs no hand-off warning."""
    _payload, warnings = build_handoff({"engagement_id": "e", "client_submission": {
        "stage_b": {"model_access_mode": "hosted_api", "model_reference": {
            "provider": "google_gemini", "model_id": "gemini-2.5-pro",
            "revision": "002"}}}})
    assert not warnings
