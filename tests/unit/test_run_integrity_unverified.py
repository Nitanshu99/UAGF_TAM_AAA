"""A run nothing independently checked is not fit to hand on.

``stub_artefact_ids`` catches an artefact nothing *produced*. It cannot see an
artefact nothing *checked*: the Verifier fails soft, and its deterministic
rubric returns a verdict byte-identical to a judged one. On 2026-09-09 a
Mariposa run lost its provider mid-engagement — 34 of 54 calls failing through
``429`` → ``503`` → ``404``, every narrative section fallen back, **10 of 17**
critiques written by the rubric — and was still stamped
``suitable_for_handoff: True``. A healthy run of the same case carries zero.
"""
from __future__ import annotations

import pytest

from aaa.platform.state.run_integrity import build_run_integrity, fallback_critique_ids


def _state(critiques: dict) -> dict:
    """An otherwise-clean run carrying the given critiques."""
    return {
        "phase_artefacts": {"T14_governance_findings": {"uri": "minio://x",
                                                        "sha256": "abc"}},
        "verifier_critiques": critiques,
    }


HEALTHY = _state({
    "T14_governance_findings": {"verdict": "accept", "llm_fallback_mode": False},
    "T17_compliance_matrix": {"verdict": "accept_with_notes", "llm_fallback_mode": False},
})

QUOTA_EXHAUSTED = _state({
    "T14_governance_findings": {"verdict": "accept", "llm_fallback_mode": True},
    "T17_compliance_matrix": {"verdict": "unverified"},
    "T18_audit_report": {"verdict": "unverified"},
    "T09_model_card": {"verdict": "accept", "llm_fallback_mode": False},
})


def test_the_run_that_was_wrongly_stamped_fit_is_now_refused():
    """The acceptance criterion, stated as an assertion."""
    assert build_run_integrity(QUOTA_EXHAUSTED)["suitable_for_handoff"] is False


def test_a_healthy_run_is_still_fit():
    """The gate must not start refusing runs that were always fine."""
    integrity = build_run_integrity(HEALTHY)
    assert integrity["suitable_for_handoff"] is True
    assert integrity["fallback_critique_ids"] == []


def test_the_block_names_which_artefacts_went_unchecked():
    """A consumer has to be able to see *what* was not verified, not just that."""
    ids = build_run_integrity(QUOTA_EXHAUSTED)["fallback_critique_ids"]
    assert ids == ["T14_governance_findings", "T17_compliance_matrix", "T18_audit_report"]


@pytest.mark.parametrize("critique", [
    {"verdict": "accept", "llm_fallback_mode": True},
    {"verdict": "unverified"},
])
def test_both_ways_a_critique_goes_unwritten_are_caught(critique):
    """The rubric authored it, or it never ran — neither is an independent check."""
    assert fallback_critique_ids(_state({"T09_model_card": critique})) == ["T09_model_card"]


def test_a_stub_artefact_still_bars_the_hand_off_on_its_own():
    """The original rule is untouched; this only adds a second way to fail it."""
    state = {"phase_artefacts": {"T02_system_card": {"uri": "", "sha256": "stub"}},
             "verifier_critiques": {}}
    integrity = build_run_integrity(state)
    assert integrity["suitable_for_handoff"] is False
    assert integrity["stub_artefact_ids"] == ["T02_system_card"]


def test_a_run_with_no_critiques_recorded_is_not_falsely_accused():
    """Absent critiques are not fallback critiques; other gates own that case."""
    assert fallback_critique_ids({"verifier_critiques": {}}) == []
    assert fallback_critique_ids({}) == []
