"""Fix 42 — a reply must carry what its output contract names (R4, R10).

One unchanged prompt, five cases, three shapes:

    case 01 #039  {"tool": "robustness_probe", "args": {…}, "request_id": …}   fallback
    case 02 #016  a correct Report                                             ok
    case 03 #039  {"tool_calls": [{"name": …, "arguments": …}]}                fallback
    case 04 #025  a correct Report                                             ok
    case 05 #028  a correct Report                                             ok

Three of five. Fix 28 enumerated the shapes a wrong reply *had* taken, and a
model has more ways to be wrong than a list can hold — two of these were not on
it. So the test is inverted: not "is this one of the wrong shapes?" but "does it
carry what the contract names?".
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aaa.tools.evidence_retrieval.terminal_round import (
    OutputContractNotMetError,
    RetrievalPlanNotAnsweredError,
    close_retrieval,
    contract_unmet,
)

#: The cybersecurity spawn's contract, verbatim from `cyber_agent/llm.py`.
CONTRACT = ("security_narrative", "summary")

#: The three replies the run actually produced, verbatim.
TOOL_REQUEST = {"tool": "robustness_probe",
                "args": {"model_uri": "minio://x/model.pkl", "modality": "tabular"},
                "request_id": "req-1"}
TOOL_CALLS = {"tool_calls": [{"name": "prompt_injection_suite",
                              "arguments": {"attack_type": "jailbreak"}}]}
BARE_PLAN = {"regulatory_queries": [
    "Article 15 accuracy robustness cybersecurity requirements EU AI Act"]}
GOOD_REPORT = {"security_narrative": "Two probes degraded accuracy by 4.1pp …",
               "blocking_findings": []}

WRONG_SHAPES = {"tool request (case 01 #039)": TOOL_REQUEST,
                "tool_calls (case 03 #039)": TOOL_CALLS,
                "bare retrieval plan (Q4)": BARE_PLAN}


class _Agent:
    """Serves the *re-prompt* replies; the first reply is passed to close_retrieval."""

    name = "CyberSecurityAgent"

    def __init__(self, *replies: Any) -> None:
        self.replies = list(replies) or [{}]
        self.calls = 0
        self.payloads: list[dict] = []

    async def acompletion_json(self, _prompt: str, payload: dict) -> Any:
        self.calls += 1
        self.payloads.append(payload)
        return self.replies[min(self.calls - 1, len(self.replies) - 1)]


def _close(agent: _Agent, first: Any, contract=CONTRACT):
    return asyncio.run(close_retrieval(agent, "cyber", {"declaration_summary": {}},
                                       first, contract))


# --------------------------------------------------------------------------- #
# the test is positive
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name,reply", sorted(WRONG_SHAPES.items()))
def test_each_observed_wrong_shape_fails_the_contract(name, reply):
    assert contract_unmet(reply, CONTRACT) is True


def test_a_correct_report_meets_it():
    assert contract_unmet(GOOD_REPORT, CONTRACT) is False


def test_an_empty_contracted_key_is_not_an_answer():
    """`summary: ""` is the shape a `.get()` used to swallow."""
    assert contract_unmet({"summary": ""}, CONTRACT) is True
    assert contract_unmet({"summary": "   "}, CONTRACT) is True


def test_a_caller_declaring_no_contract_asserts_nothing():
    assert contract_unmet(TOOL_REQUEST, ()) is False


def test_a_non_dict_reply_meets_no_contract():
    assert contract_unmet("a sentence", CONTRACT) is True
    assert contract_unmet(None, CONTRACT) is True


# --------------------------------------------------------------------------- #
# re-prompted once, then refused loudly
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name,reply", sorted(WRONG_SHAPES.items()))
def test_a_wrong_shape_is_re_prompted_once_and_then_accepted(name, reply):
    agent = _Agent(GOOD_REPORT)
    assert _close(agent, reply) == GOOD_REPORT
    assert agent.calls == 1  # exactly one re-prompt


@pytest.mark.parametrize("name,reply", sorted(WRONG_SHAPES.items()))
def test_a_wrong_shape_twice_is_refused_never_filed(name, reply):
    agent = _Agent(reply)
    with pytest.raises((OutputContractNotMetError, RetrievalPlanNotAnsweredError)):
        _close(agent, reply)
    assert agent.calls == 1


def test_a_correct_reply_costs_exactly_one_call():
    agent = _Agent()
    assert _close(agent, GOOD_REPORT) == GOOD_REPORT
    assert agent.calls == 0  # nothing re-prompted


def test_the_re_prompt_states_the_contract():
    agent = _Agent(GOOD_REPORT)
    _close(agent, TOOL_REQUEST)
    stated = agent.payloads[0]["output_contract"]
    assert stated["required_any_of"] == list(CONTRACT)
    assert "security_narrative" in stated["notice"]
    assert "ran before you were invoked" in stated["notice"]


def test_the_refusal_is_logged_at_error(caplog):
    agent = _Agent(TOOL_CALLS)
    with caplog.at_level("ERROR"):
        with pytest.raises(OutputContractNotMetError):
            _close(agent, TOOL_CALLS)
    errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(errors) == 2
    assert "not the artefact it was asked for" in errors[0].getMessage()
    assert "No artefact is filed" in errors[1].getMessage()


def test_a_plan_is_still_refused_as_a_plan():
    """The two failures share one re-prompt but keep their own exceptions."""
    agent = _Agent(BARE_PLAN)
    with pytest.raises(RetrievalPlanNotAnsweredError):
        _close(agent, BARE_PLAN)


# --------------------------------------------------------------------------- #
# one mechanism, not three
# --------------------------------------------------------------------------- #

def test_all_three_spawns_declare_their_contract_through_the_one_wrapper():
    from pathlib import Path
    source = Path("aaa/agents/tier3/narrative.py").read_text()
    assert "contract=tuple(keys)" in source
    for spawn in ("cyber_agent", "privacy_agent", "uagf_tam_l"):
        agent_src = Path(f"aaa/agents/tier3/{spawn}/llm.py").read_text()
        assert "keys=_NARRATIVE_KEYS" in agent_src


@pytest.mark.parametrize("agent", ["scope_agent", "data_auditor", "model_validator",
                                   "output_fairness", "governance_agent",
                                   "report_architect"])
def test_every_phase_agent_declares_its_contract(agent):
    from pathlib import Path
    source = Path(f"aaa/agents/tier2/{agent}/llm.py").read_text()
    assert "contract=(" in source, f"{agent} reads keys it does not assert"


# --------------------------------------------------------------------------- #
# the prompt half — the channel the model was using
# --------------------------------------------------------------------------- #

def test_no_prompt_still_says_tools_run_from_the_json_reply():
    """Fix 28 corrected the retrieval paragraph; the tools sentence was left."""
    from pathlib import Path
    prompt = Path("PROMPT.md").read_text()
    assert "Tools the runtime runs for you from your JSON reply" not in prompt
    assert prompt.count("Tools the runtime **already ran**") == 9
