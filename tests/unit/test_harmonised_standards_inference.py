"""``_infer_harmonised_standards`` against both CGSA dialects (M10).

The mock fixtures carry ``source_frameworks`` on each control; the real S5
export does not carry the field at all. The inference returned ``False`` for
every real engagement and said nothing about why, so a conservative default was
indistinguishable from a measured finding.
"""
from __future__ import annotations

import logging

from aaa.tools.cgsa_ingest.normalise_remediation import _infer_harmonised_standards

_MOCK_DIALECT = [{"domain_id": "D3", "controls": [
    {"control_id": "C11", "source_frameworks": ["EU AI Act", "ISO 42001"]}]}]

#: The control schema of the real S5 export, verbatim in shape.
_S5_DIALECT = [{"domain_id": "D3", "controls": [
    {"control_id": "C15", "control_name": "Intended-Use Requirements",
     "maturity_score": 2, "final_maturity_score": 2, "evidence_score": 2,
     "confidence": 0.7, "threshold_score": 3, "gap_severity": "critical",
     "gap_detail": "Score 2 below threshold 3 (risk tier: high).",
     "eu_ai_act_articles": ["Article 9", "Article 13"]}]}]


def test_mock_dialect_citing_iso_42001_is_true():
    """A D3 control naming the standard family is a positive determination."""
    assert _infer_harmonised_standards(_MOCK_DIALECT) is True


def test_framework_outside_d3_does_not_establish_it():
    """Only Model Development and Testing controls can establish the claim."""
    domains = [{"domain_id": "D1", "controls": [{"source_frameworks": ["ISO 42001"]}]}]
    assert _infer_harmonised_standards(domains) is False


def test_dialect_that_answers_and_says_no_is_a_silent_false():
    """A populated dialect not naming the family is a finding, so no warning."""
    domains = [{"domain_id": "D3", "controls": [{"source_frameworks": ["EU AI Act"]}]}]
    assert _infer_harmonised_standards(domains) is False


def test_real_s5_dialect_defaults_to_false_and_says_so(caplog):
    """The production dialect cannot answer; the default must be visible."""
    with caplog.at_level(logging.WARNING):
        assert _infer_harmonised_standards(_S5_DIALECT) is False
    assert "could not be determined" in caplog.text


def test_dialect_that_answers_logs_nothing(caplog):
    """A determinable payload must not emit the unavailability warning."""
    with caplog.at_level(logging.WARNING):
        _infer_harmonised_standards(_MOCK_DIALECT)
    assert "could not be determined" not in caplog.text
