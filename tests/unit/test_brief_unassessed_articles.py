"""The brief's 'could not be checked' list is the matrix's, not the ladder's raw input.

Run a2cf57 told the customer Art. 10, 13 and 15 could not be checked while the
matrix rated them FAIL (T-20260913-031).
"""
from __future__ import annotations

from aaa.agents.tier2.client_brief.overview import _overview_payload

STATE = {
    "compliance_matrix": {"Art.10": "FAIL", "Art.13": "FAIL", "Art.15": "FAIL",
                          "Art.15§1": "INSUFFICIENT_EVIDENCE", "Art.10§2(f)": "INSUFFICIENT_EVIDENCE",
                          "Art.9": "PASS"},
    "insufficient_evidence_articles": ["Art.15", "Art.10", "Art.15§1", "Art.13", "Art.10§2(f)"],
}


def test_only_matrix_insufficient_articles_are_listed() -> None:
    """A FAIL is a finding, not an article the audit failed to check."""
    listed = _overview_payload(STATE, [])["articles_that_could_not_be_checked"]
    assert sorted(listed) == ["Art.10§2(f)", "Art.15§1"]


def test_without_a_matrix_the_raw_set_is_used() -> None:
    """Early or degraded states have no matrix yet."""
    state = {"insufficient_evidence_articles": ["Art.12"]}
    assert _overview_payload(state, [])["articles_that_could_not_be_checked"] == ["Art.12"]
