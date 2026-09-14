"""Collection of the provenance answers from wizard session state."""
from __future__ import annotations

from typing import Any

import pytest

from aaa.platform.state.model_vocab import MODEL_PROVIDERS
from aaa.ui.wizard.collect.model_reference import model_reference_fields
from aaa.ui.wizard.step3.provenance.fields import state_key
from aaa.ui.wizard.step3.provenance.vendors import pin_for, questions_for


def _session(provider: str, mode: str = "hosted_api", **answers: Any) -> dict[str, Any]:
    """Build wizard session state for *provider* with *answers* filled in."""
    session: dict[str, Any] = {"s3_b_access_mode": mode, "s3_b_ref_provider": provider}
    for key, value in answers.items():
        session[state_key(key)] = value
    return session


@pytest.mark.parametrize("provider", MODEL_PROVIDERS)
def test_every_provider_is_askable(provider: str) -> None:
    """A provider in the vocabulary must never render a blank form.

    Guards against adding a provider and forgetting its question branch.
    """
    questions = questions_for(provider)
    assert questions, provider
    assert {"model_id", "revision"} <= {key for key, _label, _help in questions}
    assert pin_for(provider)


def test_no_access_mode_collects_nothing() -> None:
    """A customer who never reached the branch emits no provenance fields."""
    assert not model_reference_fields({})


def test_upload_mode_carries_no_reference() -> None:
    """An uploaded artefact needs no vendor identity."""
    assert model_reference_fields({"s3_b_access_mode": "artifact_upload"}) == {
        "model_access_mode": "artifact_upload"}


def test_blank_answers_are_dropped_not_stored_as_none() -> None:
    """The schema forbids unknown/empty keys, so blanks must not be emitted."""
    fields = model_reference_fields(_session("openai", model_id="gpt-4o-2024-08-06",
                                             revision="2024-08-06", endpoint_url=""))
    assert fields["model_reference"] == {
        "provider": "openai", "model_id": "gpt-4o-2024-08-06", "revision": "2024-08-06"}


def test_openrouter_records_the_upstream_provider() -> None:
    """One slug can be served by several providers at different quantizations."""
    fields = model_reference_fields(_session(
        "openrouter", model_id="meta-llama/llama-3.3-70b-instruct",
        revision=":free", upstream_provider="Together"))
    assert fields["model_reference"]["upstream_provider"] == "Together"


def test_gemini_round_trips_its_pinned_version() -> None:
    """Gemini aliases move underneath the caller unless a version is pinned."""
    fields = model_reference_fields(_session(
        "google_gemini", model_id="gemini-2.5-pro", revision="002"))
    assert fields["model_reference"]["revision"] == "002"


def test_structured_answers_are_carried_as_objects() -> None:
    """runtime_versions and decoding_params are objects in the schema."""
    fields = model_reference_fields(_session(
        "huggingface", mode="registry_reference", model_id="org/model",
        revision="abc123", runtime_versions="transformers 4.44"))
    assert fields["model_reference"]["runtime_versions"] == {"declared": "transformers 4.44"}
