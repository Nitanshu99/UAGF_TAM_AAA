"""Tests for the compliance-matrix node and the checkpointer."""
from __future__ import annotations

from aaa.platform.state.verdicts import FINAL_VERDICTS


def test_node_compliance_matrix_pass_verdict():
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    state = {
        "engagement_id": "eng-cm",
        "intake_completeness_score": 0.95,
        "completeness_score": None,
        "regulatory_coverage_pct": None,
        "scope_gate": {},
        "verifier_critiques": {
            "T02_system_card": {"verdict": "accept", "article_citations": ["Art.5"]},
            "T03_annex_iii_mapping": {"verdict": "accept",
                                      "article_citations": ["Art.6"]},
        },
        "phase_artefacts": {},
        "compliance_matrix": {},
        "blocking_findings": [],
        "cgsa_phase5_verdict": None,
        "cgsa_csp_satisfiable": True,
        "annex_iii_mapping": [],
        "harmonised_standards_applied": False,
        # Fix 40: the tier used to be incidental here — it is now the scope, and
        # Art. 5/Art. 6 do not bind a `minimal` engagement. The subject of this
        # test is the PASS derivation, not the tier, so the fixture states the
        # tier under which its two admitted artefacts actually claim something.
        "risk_tier": "high",
        "provider_elects_third_party": False,
    }
    result = node_compliance_matrix(state)
    assert result["final_verdict"] in FINAL_VERDICTS
    assert "Art.5" in result["compliance_matrix"]


def test_in_memory_checkpointer():
    from aaa.agents.tier1.checkpointer import make_checkpointer
    cp = make_checkpointer()
    cp.put("t1", {"a": 1})
    assert cp.get("t1") == {"a": 1}
    assert cp.get("missing") is None
