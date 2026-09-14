"""Unit tests for the downgrade-only partner-verdict merge (compliance_matrix)."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.partner_verdicts import apply_partner_verdicts


def test_partner_fail_downgrades_an_admitted_pass():
    """S6 FAIL on Art.13 overrides an existing PASS."""
    state = {"xai_evidence": {"article_verdicts": {"Art.13": "FAIL"}}}
    matrix = {"Art.13": "PASS"}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix["Art.13"] == "FAIL"
    assert changed == {"Art.13"}


def test_partner_pass_cannot_upgrade_an_existing_fail():
    """A partner PASS can never lift S5's own FAIL verdict — audit integrity."""
    state = {"xai_evidence": {"article_verdicts": {"Art.13": "PASS"}}}
    matrix = {"Art.13": "FAIL"}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix["Art.13"] == "FAIL"
    assert changed == set()


def test_absent_article_verdicts_is_a_no_op():
    """No article_verdicts key at all → matrix untouched (today's report-only path)."""
    state = {"xai_evidence": {"shap": {"top": ["age"]}}}
    matrix = {"Art.13": "PASS"}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix == {"Art.13": "PASS"}
    assert changed == set()


def test_security_partner_cannot_touch_an_article_outside_its_scope():
    """S7 (security_evidence) may only ever affect Art.15, never Art.13."""
    state = {"security_evidence": {"article_verdicts": {"Art.13": "FAIL"}}}
    matrix = {"Art.13": "PASS"}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix["Art.13"] == "PASS"  # S7 has no authority over Art.13
    assert changed == set()


def test_equal_severity_verdict_is_not_treated_as_a_change():
    """A partner proposing the same verdict already present changes nothing."""
    state = {"xai_evidence": {"article_verdicts": {"Art.13": "PASS_WITH_OBSERVATIONS"}}}
    matrix = {"Art.13": "PASS_WITH_OBSERVATIONS"}
    changed = apply_partner_verdicts(state, matrix)
    assert changed == set()


def test_partner_evidence_can_insert_a_new_row_when_s5_had_no_own_assessment():
    """No prior Art.13 row (e.g. external-mode with no internal computation) — inserted."""
    state = {"xai_evidence": {"article_verdicts": {"Art.13": "FAIL"}}}
    matrix: dict[str, str] = {}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix["Art.13"] == "FAIL"
    assert changed == {"Art.13"}


def test_unknown_verdict_value_is_ignored():
    """A malformed/unexpected verdict string never applies."""
    state = {"security_evidence": {"article_verdicts": {"Art.15": "MOSTLY_FINE"}}}
    matrix = {"Art.15": "PASS"}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix["Art.15"] == "PASS"
    assert changed == set()


def test_both_partners_apply_independently_in_one_call():
    """S6 downgrading Art.13 and S7 downgrading Art.15 both land in one pass."""
    state = {"xai_evidence": {"article_verdicts": {"Art.13": "FAIL"}},
            "security_evidence": {"article_verdicts": {"Art.15": "INSUFFICIENT_EVIDENCE"}}}
    matrix = {"Art.13": "PASS", "Art.15": "PASS"}
    changed = apply_partner_verdicts(state, matrix)
    assert matrix == {"Art.13": "FAIL", "Art.15": "INSUFFICIENT_EVIDENCE"}
    assert changed == {"Art.13", "Art.15"}
