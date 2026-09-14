"""Bounded plan-then-retrieve (ReAct) loop in evidence_retrieval."""
from __future__ import annotations

import asyncio

from aaa.tools.evidence_retrieval import acompletion_json_react


class _FakeAgent:
    name = "Fake"

    def __init__(self):
        self.calls = 0

    async def acompletion_json(self, prompt_name, payload):
        self.calls += 1
        if self.calls == 1:
            return {"retrieval_plan": {"regulatory_queries": ["q"],
                                       "client_doc_queries": []}}
        return {"done": True,
                "regulatory_hits_seen": len(payload.get("regulatory_hits", []))}


class _FakeRag:
    def search(self, query, top_k=3):
        return [{"source_uri": "euaiact://Article_9", "text": "…"}]


def test_react_expands_once_then_stops():
    agent = _FakeAgent()
    result = asyncio.run(acompletion_json_react(
        agent, "p", {"regulatory_hits": [{"source_uri": "euaiact://Article_10"}]},
        rag=_FakeRag(), engagement_id="", rounds=1,
    ))
    assert agent.calls == 2  # initial + one expansion
    assert result["regulatory_hits_seen"] == 2


def test_react_is_noop_without_retrieval_plan():
    class _NoPlan:
        name = "NoPlan"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):
            type(self).calls += 1
            return {"done": True}

    asyncio.run(acompletion_json_react(_NoPlan(), "p", {}, rag=_FakeRag(), rounds=1))
    assert _NoPlan.calls == 1  # single shot, no expansion
