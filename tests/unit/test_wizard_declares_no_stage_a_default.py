"""T-20260914-021: the wizard records no Stage A declaration the provider did not make.

Step 3 seeded version ``0.1.0``, modality ``tabular``, risk tier ``limited`` and
deployment context ``b2b`` whenever the documents and the questionnaire were silent,
and the three selects reset an unrecognised value to their first option. Submitted
unchanged, each became the provider's own declaration.
"""
from __future__ import annotations

import inspect

import pytest

from aaa.ui.wizard import loaders
from aaa.ui.wizard.collect.stage import a as stage_a_module
from aaa.ui.wizard.step3 import required_fields
from aaa.ui.wizard.step3 import state as state_module
from aaa.ui.wizard.step3.stage_a import classification

_UNDECLARED = ("version", "declared_modality", "declared_risk_tier", "deployment_context")


@pytest.fixture(name="session")
def _session(monkeypatch: pytest.MonkeyPatch) -> dict:
    """One dict standing in for ``st.session_state`` in every module that reads it."""
    session: dict = {}
    for module in (loaders, state_module, stage_a_module, classification):
        monkeypatch.setattr(module.st, "session_state", session)
    monkeypatch.setattr(stage_a_module, "prior_assessment_id", lambda: None)
    return session


def test_silent_sources_seed_nothing(session: dict) -> None:
    """No extraction and no answer leave every one of the four undeclared."""
    state_module.initialise_step3_state({}, {})
    assert [session[f"s3_a_{key}"] for key in _UNDECLARED] == ["", None, None, None]


def test_declared_values_are_kept(session: dict) -> None:
    """What the documents and the questionnaire say still reaches the form."""
    extraction = {"stage_a_partial": {"version": "1.0.0", "declared_modality": "llm",
                                      "declared_risk_tier": "high"}}
    state_module.initialise_step3_state(extraction, {"deployment_context": "b2c"})
    assert [session[f"s3_a_{key}"] for key in _UNDECLARED] == ["1.0.0", "llm", "high", "b2c"]


def test_collector_without_the_keys_declares_nothing(session: dict) -> None:
    """Dropped widget keys are collected as undeclared, never as an option."""
    payload = stage_a_module.collect_stage_a()
    assert [payload[key] for key in _UNDECLARED] == ["", None, None, None]


def test_an_unknown_value_is_cleared_not_replaced(session: dict) -> None:
    """An extraction the schema rejects is cleared; a valid one is left alone."""
    session.update({"s3_a_declared_modality": "vision", "s3_a_declared_risk_tier": "high"})
    classification._ensure_valid("s3_a_declared_modality", ["tabular", "llm"])
    classification._ensure_valid("s3_a_declared_risk_tier", ["high", "limited"])
    assert session["s3_a_declared_modality"] is None
    assert session["s3_a_declared_risk_tier"] == "high"


def test_undeclared_selects_block_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """The run gate names each undeclared select by the label the form shows."""
    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {
        "provider_name": "P", "system_name": "S", "version": "1.0", "intended_purpose": "x",
        "declared_modality": None, "declared_risk_tier": None, "deployment_context": None})
    assert required_fields._required_stage_a_blanks() == [
        "AI modality", "Self-assessed risk tier", "Deployment context"]


def test_no_select_preselects_an_option() -> None:
    """Every Stage A select renders with no option chosen (``index=None``)."""
    from aaa.ui.wizard.step2 import form

    assert inspect.getsource(classification.render_classification).count("index=None") == 3
    assert "index=None" in inspect.getsource(form.render_questions)
