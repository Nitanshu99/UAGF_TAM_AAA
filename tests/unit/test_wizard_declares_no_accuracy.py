"""T-20260914-020: the wizard never records an accuracy the provider did not declare.

The Stage B metrics field was prefilled with ``{"accuracy": 0.8}`` whenever the
documents yielded no Annex IV §4 metrics, and the collector fell back to the same
literal. Submitted unchanged, 0.8 became the provider's declared accuracy.
"""
from __future__ import annotations

import pytest

from aaa.ui.wizard import loaders
from aaa.ui.wizard.collect.stage import b as stage_b_module
from aaa.ui.wizard.step3 import state as state_module


@pytest.fixture(name="session")
def _session(monkeypatch: pytest.MonkeyPatch) -> dict:
    """One dict standing in for ``st.session_state`` in every module that reads it."""
    session: dict = {}
    for module in (loaders, state_module, stage_b_module):
        monkeypatch.setattr(module.st, "session_state", session)
    return session


@pytest.mark.parametrize("extracted", [None, "", {}])
def test_no_extracted_metrics_means_none_declared(session: dict, extracted) -> None:
    """Nothing extracted seeds an empty object, and collects as no metrics."""
    partial = {} if extracted is None else {"accuracy_metrics": extracted}
    state_module.initialise_step3_state({"stage_b_partial": partial}, {})
    assert session["s3_b_accuracy_metrics_raw"] == "{}"
    assert stage_b_module.collect_stage_b()["accuracy_metrics"] == {}


def test_extracted_metrics_are_kept(session: dict) -> None:
    """A declared figure still reaches the dossier unchanged."""
    extraction = {"stage_b_partial": {"accuracy_metrics": {"accuracy": 0.912}}}
    state_module.initialise_step3_state(extraction, {})
    assert stage_b_module.collect_stage_b()["accuracy_metrics"] == {"accuracy": 0.912}


def test_collector_without_the_key_declares_nothing(session: dict) -> None:
    """A dropped widget key is not replaced by a sample figure."""
    assert stage_b_module.collect_stage_b()["accuracy_metrics"] == {}
