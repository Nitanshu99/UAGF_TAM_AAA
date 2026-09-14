"""CGSA retrieval failure is an evidence gap, never a governance FAIL."""
from __future__ import annotations

import asyncio
import importlib

from aaa.platform.evidence import EvidenceStore
from tests.unit.support.real_auditor_state import base_state


def test_cgsa_retrieval_failure_marks_insufficient_not_fail(monkeypatch):
    """A CGSA pull/ingest failure is an evidence-availability problem.

    The GovernanceAgent escalation must NOT stamp ``cgsa_phase5_verdict="FAIL"``
    (which the compliance matrix treats as a hard adverse FAIL).  It must
    instead mark the governance articles INSUFFICIENT_EVIDENCE so the opinion
    is a disclaimer for them, not a blanket non-conformity.
    """
    from aaa.agents.tier2 import governance_agent as gov_pkg
    from aaa.tools.cgsa_pull import CGSAPullError
    # The pull lives in `acquire` since T-20260914-062 (evaluated-export resolution).
    gov_ingest = importlib.import_module("aaa.agents.tier2.governance_agent.acquire")

    def _boom(*_a, **_k):
        raise CGSAPullError("fixture_dir_not_set", {"hint": "no fixture"})

    monkeypatch.setattr(gov_ingest, "cgsa_pull", _boom)
    agent = gov_pkg.GovernanceAgent(EvidenceStore())
    dispatch = {
        "phase_id": "P5",
        "evidence_uris": [],
        "declaration_summary": {"engagement_id": "eng-esc",
                                "cgsa_assessment_id": "cgsa-x"},
    }
    report = asyncio.run(agent.process(dispatch))
    delta = report["declaration_verification_delta"]

    # No spurious FAIL verdict is emitted on a retrieval failure.
    assert "cgsa_phase5_verdict" not in delta
    assert delta.get("cgsa_phase5_verdict") != "FAIL"
    # Governance articles are flagged for the matrix's INSUFFICIENT_EVIDENCE path.
    assert set(delta["insufficient_evidence_articles"]) == {
        "Art.9", "Art.12", "Art.17", "Art.72"
    }
    assert delta["hitl_required"] is True


def test_cgsa_retrieval_failure_yields_disclaimer_not_adverse():
    """The escalation delta routes through the matrix to a disclaimer, not FAIL."""
    from aaa.agents.tier1.phases.agent_runner import _apply_delta
    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix

    # cgsa_phase5_verdict stays unset (None) because CGSA was never ingested.
    state = base_state(cgsa_phase5_verdict=None)
    _apply_delta(state, {
        "hitl_required": True,
        "hitl_reason": "cgsa_pull failed: fixture_dir_not_set",
        "insufficient_evidence_articles": ["Art.9", "Art.12", "Art.17", "Art.72"],
        "phase_artefacts": {},
    })
    node_compliance_matrix(state)

    for art in ("Art.9", "Art.12", "Art.17", "Art.72"):
        assert state["compliance_matrix"][art] == "INSUFFICIENT_EVIDENCE"
    assert state["final_verdict"] == "DISCLAIMER_OF_OPINION"
    assert state["final_verdict"] != "FAIL"
    assert state["opinion_disclaimer"] is True
