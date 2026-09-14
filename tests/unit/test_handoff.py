"""Unit tests for the partner hand-off builder (envelope + fail-soft warnings)."""
from __future__ import annotations

import json
from pathlib import Path

from aaa.integrations.handoff import HANDOFF_SCHEMA_VERSION, build_handoff

# Committed fixtures: `data/customer/` is gitignored run output.
_FIXTURE = Path("tests/fixtures/customer_finclear/eng-01_finclear_gmbh_audit_state.json")
_DEGRADED = Path("tests/fixtures/degraded_run/eng-degraded_audit_state.json")


def _state() -> dict:
    """Load the backfilled finclear audit state (a healthy run)."""
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _degraded() -> dict:
    """Load a run whose Phase 1/5/6 delivered placeholders."""
    return json.loads(_DEGRADED.read_text(encoding="utf-8"))


def test_backfilled_fixture_satisfies_every_field_requirement() -> None:
    """A healthy finclear run satisfies every S6 field requirement and integrity check.

    Before fix F3 this test asserted ``not warnings`` against a state whose
    Phase 1 had never run, and passed — the blind spot that let a missing phase
    reach S6 as a schema complaint. It now runs against a genuinely clean state,
    so ``not warnings`` means what it says.
    """
    payload, warnings = build_handoff(_state())
    assert not warnings
    assert payload["handoff_schema_version"] == HANDOFF_SCHEMA_VERSION
    assert payload["engagement_id"] == "eng-01_finclear_gmbh"
    assert payload["audit_state"]["client_submission"]["stage_b"]["task_type"]


def test_degraded_run_is_warned_before_any_field_check() -> None:
    """A placeholder run is reported first, and names the phases that failed."""
    _, warnings = build_handoff(_degraded())
    assert "DEGRADED" in warnings[0]
    assert "P1" in warnings[0] and "P5" in warnings[0]


def test_verdict_without_phase_1_is_called_out() -> None:
    """A final verdict resting on a stubbed T02 is named as such."""
    _, warnings = build_handoff(_degraded())
    assert any("final_verdict" in w and "T02_system_card" in w for w in warnings)


def test_clean_run_raises_no_integrity_warning() -> None:
    """A run that reached every phase contributes no integrity warning."""
    payload, warnings = build_handoff(_state())
    assert not [w for w in warnings if "DEGRADED" in w]
    assert payload["run_integrity"]["suitable_for_handoff"] is True


def test_envelope_carries_the_integrity_block() -> None:
    """S6 gates on the envelope, so the block travels beside the state."""
    payload, _ = build_handoff(_degraded())
    assert payload["run_integrity"]["suitable_for_handoff"] is False
    assert payload["run_integrity"]["degraded_phases"] == ["P1", "P5", "P6"]


def test_missing_task_type_warns_but_builds() -> None:
    """A missing required field produces a warning, never an exception."""
    state = _state()
    state["client_submission"]["stage_b"]["task_type"] = None
    payload, warnings = build_handoff(state)
    assert payload["audit_state"] is state
    assert any("task_type" in w for w in warnings)


def test_binary_classification_requires_positive_label() -> None:
    """Binary classification without positive_label is flagged."""
    state = _state()
    # Cleared in both places: Stage B carries this key nested *and* top-level,
    # and "missing" means the client declared it nowhere. Blanking only the top
    # level left the nested declaration standing, which is not a missing field.
    state["client_submission"]["stage_b"]["positive_label"] = None
    state["client_submission"]["stage_b"].get("data_dictionary", {}).pop(
        "positive_label", None)
    _, warnings = build_handoff(state)
    assert any("positive_label" in w for w in warnings)


def test_a_nested_only_declaration_is_not_reported_missing() -> None:
    """A CLI bundle nests these keys and declares nothing at the top level.

    Warning on the top level alone told S6 that a supervised engagement had no
    target column, for a dossier that named one — and the same blind spot
    published an empty sensitive-feature list to the partner hand-off.
    """
    state = _state()
    stage_b = state["client_submission"]["stage_b"]
    stage_b["data_dictionary"] = {"target_column": "credit_risk", "positive_label": 1}
    stage_b["target_column"] = None
    stage_b["positive_label"] = None
    _payload, warnings = build_handoff(state)
    assert not any("target_column" in w or "positive_label" in w for w in warnings)


def test_empty_state_builds_without_warnings() -> None:
    """No model artefact → the S6 field requirements do not apply."""
    payload, warnings = build_handoff({})
    assert not warnings
    assert payload["engagement_id"] is None
