"""Tests for expanded regulatory coverage article set."""
from __future__ import annotations

from aaa.tools.regulatory_coverage import ARTICLE_SET, compute_regulatory_coverage_pct


def test_high_article_set_includes_phase_template_articles():
    required = {"Art.5", "Art.6", "Art.11", "Art.12", "Art.50", "Art.72", "Annex_IV"}
    assert required <= ARTICLE_SET["high"]


def test_annex_iv_and_art5_fallbacks_are_derived():
    state = {
        "risk_tier": "high",
        "is_llm_or_agentic": False,
        "intake_completeness_score": 0.9,
        "scope_gate": {},
        "compliance_matrix": {},
        "phase_artefacts": {},
        "verifier_critiques": {},
    }
    compute_regulatory_coverage_pct(state)
    assert state["compliance_matrix"]["Art.5"] == "PASS"
    assert state["compliance_matrix"]["Annex_IV"] == "PASS"