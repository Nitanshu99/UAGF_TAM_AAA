"""_derive_verdicts applies the downgrade-only partner-verdict merge end to end."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts


def _admitted_state(**overrides: object) -> dict:
    """An engagement where Art.13 is independently admitted (PASS) via T09."""
    state: dict = {
        "verifier_critiques": {
            "T09_model_card": {"verdict": "accept", "article_citations": ["Art.13"]}},
        "phase_artefacts": {},
    }
    state.update(overrides)
    return state


def test_partner_fail_downgrades_the_derived_pass_and_notes_the_rationale():
    """S6 FAIL on Art.13 overrides S5's own admitted PASS, with a visible rationale note."""
    state = _admitted_state(xai_evidence={"article_verdicts": {"Art.13": "FAIL"}})
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.13"] == "FAIL"
    assert "Downgraded by independent partner evidence" in state["article_evidence"]["Art.13"]["rationale"]


def test_no_partner_evidence_leaves_the_derived_verdict_untouched():
    """Absent xai_evidence/security_evidence, the matrix is exactly S5's own view."""
    state = _admitted_state()
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.13"] == "PASS"
    assert "Downgraded" not in state["article_evidence"]["Art.13"]["rationale"]


def test_partner_pass_cannot_override_a_material_finding_fail():
    """A material finding drives FAIL; a partner PASS opinion cannot undo it."""
    state = _admitted_state(
        blocking_findings=[{"materiality": "material", "finding_id": "P3-1",
                            "eu_ai_act_articles": ["Art.13"]}],
        xai_evidence={"article_verdicts": {"Art.13": "PASS"}})
    _derive_verdicts(state)
    assert state["compliance_matrix"]["Art.13"] == "FAIL"
