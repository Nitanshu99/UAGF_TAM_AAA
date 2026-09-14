"""Fix 28 (Q4) — a tier-3 spawn's reply must be a report, not a retrieval plan.

Both spawns that ran on case 01 replied with plans where a report was due.
`CyberSecurityAgent` returned `{"regulatory_queries": [...]}` — 97 characters,
no wrapper — and `PrivacyDPOAgent` returned `{"retrieval_plan": {...}}`. Neither
reply was recognised as a plan: the spawns called `acompletion_json` directly, so
fix 10's terminal notice and closing re-prompt never applied to them, and the
bare shape was not recognised anywhere at all. Both artefacts recorded
`llm_fallback_mode=true` and kept a prompt-metadata string where their reasoning
should have been.
"""
from __future__ import annotations

from typing import Any

import pytest

from aaa.agents.tier3.cyber_agent.llm import run_llm_synthesis as cyber_synth
from aaa.agents.tier3.narrative import SPAWN_RETRIEVAL_CLOSED, with_narrative
from aaa.agents.tier3.privacy_agent.llm import run_llm_synthesis as privacy_synth
from aaa.agents.tier3.uagf_tam_l.llm import run_llm_synthesis as tam_l_synth
from aaa.tools.evidence_retrieval.terminal_round import plan_in

#: The two replies the run actually produced, quoted from the audit trail.
CYBER_REPLY: dict[str, Any] = {
    "regulatory_queries": ["Article 15 accuracy robustness cybersecurity "
                           "requirements EU AI Act"]}
PRIVACY_REPLY: dict[str, Any] = {
    "retrieval_plan": {
        "regulatory_queries": ["Article 10 paragraph 5 special category data "
                               "lawful basis EU AI Act"],
        "client_doc_queries": ["DPIA documentation FinClear"]}}

#: Positional args each spawn's synthesis takes after the agent.
_ARGS: dict[Any, tuple] = {cyber_synth: ({}, [], None, []),
                           privacy_synth: ({}, {}, []),
                           tam_l_synth: ({}, {})}
_KEYS = {cyber_synth: "security_narrative", privacy_synth: "privacy_narrative",
         tam_l_synth: "evaluation_narrative"}


class ScriptedAgent:
    """Returns each scripted reply in turn, recording the payloads it was given."""

    name = "ScriptedAgent"

    def __init__(self, *replies: dict[str, Any]):
        self._replies = list(replies)
        self.payloads: list[dict[str, Any]] = []

    async def acompletion_json(self, prompt_name: str, payload: Any,
                               **_: Any) -> dict[str, Any]:
        """Return the next scripted reply, repeating the last one when exhausted."""
        self.payloads.append(payload)
        return self._replies[min(len(self.payloads) - 1, len(self._replies) - 1)]

    def prompt_note(self, prompt_name: str, fallback: bool) -> str:
        """Mimic BaseAgent's provenance note."""
        return f"[prompt={prompt_name} fallback={fallback}]"


# ── recognising a plan in either shape ───────────────────────────────────────

def test_the_bare_plan_the_run_returned_is_recognised():
    """97 characters of queries with no wrapper — read as an answer until now."""
    assert plan_in(CYBER_REPLY) == CYBER_REPLY


def test_the_wrapped_plan_is_recognised():
    assert plan_in(PRIVACY_REPLY) == PRIVACY_REPLY["retrieval_plan"]


@pytest.mark.parametrize("reply", [
    {"security_narrative": "The injection suite found no bypass."},
    {"summary": "done", "regulatory_queries": ["Article 15"]},  # content beside queries
    {}, None, "not a dict", [],
])
def test_an_answer_is_not_mistaken_for_a_plan(reply):
    assert plan_in(reply) is None


# ── the spawns get the terminal round ────────────────────────────────────────

@pytest.mark.parametrize("synth", [cyber_synth, privacy_synth, tam_l_synth])
async def test_every_spawn_is_told_retrieval_is_closed_before_it_answers(synth):
    """A spawn has no RAG at all, so its first round is also its last."""
    agent = ScriptedAgent({_KEYS[synth]: "interpreted"})

    await synth(agent, *_ARGS[synth])

    expansion = agent.payloads[0]["retrieval_expansion"]
    assert expansion["retrieval_closed"] is True
    assert expansion["final_round"] is True
    assert "no retrieval channel" in expansion["notice"]
    assert expansion == SPAWN_RETRIEVAL_CLOSED


@pytest.mark.parametrize("synth,planned", [(cyber_synth, CYBER_REPLY),
                                           (privacy_synth, PRIVACY_REPLY),
                                           (tam_l_synth, PRIVACY_REPLY)])
async def test_a_plan_is_re_prompted_once_and_the_answer_is_kept(synth, planned):
    """The run's own replies, replayed: a plan now buys a second chance."""
    agent = ScriptedAgent(planned, {_KEYS[synth]: "Art. 15 robustness holds."})

    narrative, note = await synth(agent, *_ARGS[synth])

    assert narrative == "Art. 15 robustness holds."
    assert "fallback=False" in note
    assert len(agent.payloads) == 2


@pytest.mark.parametrize("synth,planned", [(cyber_synth, CYBER_REPLY),
                                           (privacy_synth, PRIVACY_REPLY)])
async def test_a_model_that_plans_twice_falls_back_loudly(synth, planned, caplog):
    """Never silently: the artefact keeps its measured numbers and says so."""
    agent = ScriptedAgent(planned)

    narrative, note = await synth(agent, *_ARGS[synth])

    assert narrative is None
    assert "fallback=True" in note
    assert len(agent.payloads) == 2          # tried, then gave up
    assert any("retrieval_plan" in r.message or "no narrative" in r.message
               for r in caplog.records)


@pytest.mark.parametrize("synth,planned", [(cyber_synth, CYBER_REPLY),
                                           (privacy_synth, PRIVACY_REPLY)])
async def test_no_part_of_a_plan_reaches_the_artefact(synth, planned):
    """Q4's actual harm: a plan filed where the reasoning belongs."""
    agent = ScriptedAgent(planned)

    narrative, note = await synth(agent, *_ARGS[synth])
    artefact = with_narrative({"probes": ["real measurement"]}, narrative, note)

    assert "regulatory_queries" not in artefact["tier3_llm_narrative"]
    assert artefact["tier3_llm_narrative"] == note
    assert artefact["probes"] == ["real measurement"]     # the numbers survive


@pytest.mark.parametrize("synth", [cyber_synth, privacy_synth, tam_l_synth])
async def test_a_provider_failure_still_falls_back_as_it_always_did(synth):
    class Broken(ScriptedAgent):
        async def acompletion_json(self, prompt_name, payload, **_):
            raise RuntimeError("provider down")

    narrative, note = await synth(Broken(), *_ARGS[synth])

    assert narrative is None
    assert "fallback=True" in note


@pytest.mark.parametrize("synth", [cyber_synth, privacy_synth, tam_l_synth])
async def test_an_answering_model_costs_exactly_one_call(synth):
    agent = ScriptedAgent({_KEYS[synth]: "interpreted"})

    narrative, _ = await synth(agent, *_ARGS[synth])

    assert narrative == "interpreted"
    assert len(agent.payloads) == 1
