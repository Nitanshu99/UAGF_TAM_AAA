"""Unit tests for the step 4 evidence-status panel's status-line rendering."""
from __future__ import annotations

from aaa.ui.wizard.step4.evidence import _status_line


def test_not_required_shows_badge_and_reason():
    """A gated-out section shows a distinct badge plus its reason."""
    line = _status_line({"evidence_source": "not_required", "reason": "no model artefact"})
    assert "not required" in line
    assert "no model artefact" in line


def test_internal_and_external_get_distinct_labels():
    """Internal and external sources render visibly different status text."""
    internal = _status_line({"evidence_source": "internal"})
    external = _status_line({"evidence_source": "external"})
    assert "internal analysis" in internal
    assert "partner analysis" in external
    assert internal != external


def test_error_stub_mentions_could_not_be_collected():
    """A provider error stub reads clearly, distinct from not-required."""
    line = _status_line({"evidence_source": "external", "error": "not_found"})
    assert "could not be collected" in line
    assert "not required" not in line


def test_missing_evidence_document_does_not_crash():
    """None (no landing zone at all) renders a generic no-evidence status."""
    assert "no evidence" in _status_line(None)
