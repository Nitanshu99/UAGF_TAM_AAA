"""A dead provider must cost a few calls, not one per requirement.

``build_brief`` makes one call per audited article. Unbounded, a provider that is
not answering is asked seventeen times: with this agent's 420 s ceiling that is
**~2 hours** to produce a brief that was deterministic from its first section,
and it made every pipeline test seventeen doomed calls longer — which is how it
was found, one test sitting at 2 m 51 s and 11 % CPU.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier2.client_brief.agent import FAILURES_BEFORE_GIVING_UP, ClientBriefAgent

_STATE: dict = {
    "engagement_id": "eng-test",
    "final_verdict": "FAIL",
    "compliance_matrix": {f"Art.{n}": "FAIL" for n in range(1, 13)},
    "article_evidence": {},
    "blocking_findings": [],
    "client_submission": {"stage_a": {"system_name": "Sorter"}},
}


def _agent(monkeypatch, outcomes):
    """A ClientBriefAgent whose section writer yields *outcomes* in order."""
    agent = ClientBriefAgent(evidence_store=None)
    calls: list[str] = []

    async def _write(_self, bundle, _rag=None, _engagement_id=""):
        calls.append(bundle["article"])
        written = outcomes(len(calls))
        return {"article": bundle["article"], "subject": bundle["subject"],
                "verdict": bundle["verdict"], "llm_written": written,
                "headline": "x" if written else None}

    monkeypatch.setattr("aaa.agents.tier2.client_brief.compose.write_article_section", _write)

    async def _overview(_self, _state, _sections):
        calls.append("OVERVIEW")
        return {"overall_explanation": "x", "llm_written": True}

    monkeypatch.setattr("aaa.agents.tier2.client_brief.compose.write_overview", _overview)
    return agent, calls


@pytest.mark.asyncio
async def test_a_dead_provider_stops_being_asked(monkeypatch):
    """The acceptance criterion: 12 articles, but not 12 calls."""
    agent, calls = _agent(monkeypatch, lambda _n: False)
    await agent.build_brief(_STATE, "eng-test")
    assert len(calls) == FAILURES_BEFORE_GIVING_UP
    assert "OVERVIEW" not in calls, "the opening was attempted after the breaker tripped"


@pytest.mark.asyncio
async def test_every_requirement_still_reaches_the_document(monkeypatch):
    """Giving up on calls must never mean giving up on sections."""
    agent, _ = _agent(monkeypatch, lambda _n: False)
    brief = await agent.build_brief(_STATE, "eng-test")
    for article in _STATE["compliance_matrix"]:
        assert article in brief


@pytest.mark.asyncio
async def test_a_healthy_provider_is_asked_for_every_section(monkeypatch):
    """The breaker must be invisible when nothing is failing."""
    agent, calls = _agent(monkeypatch, lambda _n: True)
    await agent.build_brief(_STATE, "eng-test")
    assert len(calls) == len(_STATE["compliance_matrix"]) + 1  # + the opening


@pytest.mark.asyncio
async def test_an_isolated_failure_does_not_trip_it(monkeypatch):
    """One bad minute is what fix 39's retry and the 504 reclassification absorb."""
    agent, calls = _agent(monkeypatch, lambda n: n % 2 == 0)
    await agent.build_brief(_STATE, "eng-test")
    assert len(calls) == len(_STATE["compliance_matrix"]) + 1


@pytest.mark.asyncio
async def test_the_counter_resets_on_a_success(monkeypatch):
    """Two failures, a success, then two more must not add up to a trip."""
    pattern = {1: False, 2: False, 3: True}
    agent, calls = _agent(monkeypatch, lambda n: pattern.get(n, False))
    await agent.build_brief(_STATE, "eng-test")
    assert len(calls) == 3 + FAILURES_BEFORE_GIVING_UP
