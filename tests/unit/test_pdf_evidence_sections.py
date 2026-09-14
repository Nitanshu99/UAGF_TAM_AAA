"""Unit tests for the PDF's explainability/security evidence sections."""
from __future__ import annotations

from reportlab.platypus import Paragraph

from aaa.tools.report_render.pdf.evidence import build_evidence


def _flatten_text(flow: list) -> str:
    """Join every Paragraph's text in *flow* for substring assertions."""
    return " ".join(getattr(f, "text", "") for f in flow if isinstance(f, Paragraph))


def test_not_required_shows_the_reason_not_an_empty_section():
    """A gated-out section renders its reason, not a blank/silent gap."""
    state = {"xai_evidence": {"evidence_source": "not_required",
                              "reason": "no evaluable model artefact was submitted"},
             "security_evidence": {"evidence_source": "not_required",
                                   "reason": "Art. 15 is not in scope"}}
    text = _flatten_text(build_evidence(state))
    assert "Not required for this engagement" in text
    assert "no evaluable model artefact was submitted" in text
    assert "Art. 15 is not in scope" in text


def test_error_stub_shows_unavailable_notice():
    """An external-provider failure still renders a clear notice."""
    state = {"xai_evidence": {"evidence_source": "external", "error": "not_found"},
             "security_evidence": {"evidence_source": "external", "error": "timeout"}}
    text = _flatten_text(build_evidence(state))
    assert "could not be collected" in text


def test_populated_evidence_renders_a_table_not_the_reason_line():
    """Real evidence data does not get mistaken for a not-required/error stub."""
    state = {"xai_evidence": {"evidence_source": "internal",
                              "explainability_report": {"uri": "minio://x/t10"}},
             "security_evidence": {"evidence_source": "internal",
                                   "robustness_report": {"uri": "minio://x/t11"}}}
    text = _flatten_text(build_evidence(state))
    assert "Not required for this engagement" not in text
    assert "could not be collected" not in text
