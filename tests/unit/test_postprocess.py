"""Unit tests for the guarded partner-response extraction (aaa.integrations.postprocess)."""
from __future__ import annotations

import logging

from aaa.integrations.postprocess import extract_partner_sections

_REAL_STATE_SHAPE = {"engagement_id": "eng-1", "client_submission": {"stage_a": {}},
                     "final_verdict": "PASS"}


def test_full_echo_extracts_only_the_named_section():
    """A full audit-state echo yields only the section's own content."""
    echo = {**_REAL_STATE_SHAPE, "xai_evidence": {"shap": {"top": ["age"]}},
           "other_junk": "should never appear"}
    result = extract_partner_sections(echo, "xai_evidence", "xai")
    assert result == {"shap": {"top": ["age"]}}


def test_wrapped_audit_state_echo_is_also_recognised():
    """An echo wrapped as {"audit_state": {...}} (mirroring our own handoff) works too."""
    echo = {"audit_state": {**_REAL_STATE_SHAPE,
                            "security_evidence": {"attack_taxonomy": ["prompt_injection"]}}}
    result = extract_partner_sections(echo, "security_evidence", "security")
    assert result == {"attack_taxonomy": ["prompt_injection"]}


def test_clobber_attempt_is_discarded_and_logged(caplog):
    """An echo that also carries final_verdict never surfaces it — only a warning."""
    echo = {**_REAL_STATE_SHAPE, "final_verdict": "FAIL",
           "xai_evidence": {"shap": {"top": ["age"]}}}
    with caplog.at_level(logging.WARNING):
        result = extract_partner_sections(echo, "xai_evidence", "xai")
    assert result == {"shap": {"top": ["age"]}}
    assert "final_verdict" not in result
    assert any("final_verdict" in rec.message for rec in caplog.records)


def test_bare_section_response_still_extracts_correctly():
    """No client_submission sentinel → treated as a bare section, unwrapped as-is."""
    bare = {"shap": {"top": ["age"]}}
    assert extract_partner_sections(bare, "xai_evidence", "xai") == bare


def test_missing_section_in_full_echo_returns_empty_dict():
    """A full echo that never populated the section yields {} (not a crash)."""
    echo = dict(_REAL_STATE_SHAPE)
    assert extract_partner_sections(echo, "xai_evidence", "xai") == {}


def test_non_dict_response_returns_empty_dict():
    """A non-dict response (e.g. a string or list) never raises."""
    assert extract_partner_sections("not a dict", "xai_evidence", "xai") == {}
    assert extract_partner_sections(None, "xai_evidence", "xai") == {}
