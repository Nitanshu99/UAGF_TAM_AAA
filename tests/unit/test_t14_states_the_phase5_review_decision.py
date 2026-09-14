"""T14 records the Phase 5 human-review decision the report acts on.

T14 said hitl_required false while Phase 5 escalated (T-20260913-040).
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.decision import phase5_hitl
from aaa.tools.cgsa_ingest import IngestResult


def _result(**state: object) -> IngestResult:
    """An ingest result carrying *state* as its delta."""
    return IngestResult(payload={}, state_delta=dict(state))


def test_a_fail_verdict_requires_review_with_a_reason() -> None:
    """FAIL escalates and says so."""
    required, reason = phase5_hitl(_result(cgsa_phase5_verdict="FAIL"), {}, False)
    assert required is True and "FAIL" in (reason or "")


def test_a_clean_phase_requires_none() -> None:
    """No trigger, no review, no reason."""
    assert phase5_hitl(_result(cgsa_phase5_verdict="PASS"), {}, False) == (False, None)


def test_a_blocking_follow_up_is_named_not_generic() -> None:
    """A follow-up escalation names itself rather than a generic reason."""
    result = _result(cgsa_phase5_verdict="PASS", cgsa_recommended_follow_up=[
        {"urgency": "required_before_report_completion"}])
    required, reason = phase5_hitl(result, {}, False)
    assert required and reason == "A CGSA follow-up is required before report completion."


def test_the_artefact_builder_stamps_the_same_decision() -> None:
    """build_and_store_artefacts writes the decision onto T14 before storing it."""
    from aaa.agents.tier2.governance_agent import artefacts

    stored: dict = {}

    class _Store:
        def store_artefact(self, _eng, _phase, tid, payload, _agent):
            """Keep what would be persisted."""
            stored[tid] = payload
            return f"minio://x/{tid}"

    agent = type("A", (), {"store": _Store(), "name": "GovernanceAgent"})()
    original = (artefacts.build_t14, artefacts.build_t15)
    artefacts.build_t14 = lambda *a, **k: {"phase5_narrative_summary": "", "hitl_required": False}
    artefacts.build_t15 = lambda *a, **k: {"observations": []}
    try:
        artefacts.build_and_store_artefacts(agent, "eng", _result(cgsa_phase5_verdict="FAIL"),
                                            {}, {}, True, "now", {}, None, "")
    finally:
        artefacts.build_t14, artefacts.build_t15 = original
    assert stored["T14_governance_findings"]["hitl_required"] is True
    assert "risk_tier" in stored["T14_governance_findings"]["hitl_reason"]
