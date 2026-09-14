"""Fix 18 — the retrieval ceiling is arbitrated by the clock, not counted out.

``rounds=1`` gave a phase agent one chance to correct a missed retrieval. Raising
that is the obvious remedy and the dangerous one: the phase timeout covers every
LLM call the loop makes, and a phase that overruns it returns **no report at
all** — finding P4, where Phase 3's rerun spent 106.3 s then 78.5 s against a
180 s budget and produced nothing. In the post-fix run a phase-agent call cost a
median of 52.1 s and a maximum of 106.3 s, so a third call is not free.

Two gates therefore decide each round instead of the number: whether it fits the
budget left, estimated from the slowest call this loop has already made, and
whether the previous one returned anything the model did not already hold. The
tests below pin both, the honesty of the terminal notice when the budget closes
retrieval early, and the fact that an unbound deadline means *no* deadline.
"""
from __future__ import annotations

import asyncio
import pathlib
import time

from aaa.platform.phase_budget import bind_phase_deadline, remaining_seconds
from aaa.tools.evidence_retrieval import acompletion_json_react
from aaa.tools.evidence_retrieval import rounds as rounds_mod
from aaa.tools.evidence_retrieval.dedup import hit_keys
from aaa.tools.evidence_retrieval.rounds import (
    MAX_ROUNDS,
    is_final_round,
    learned_something,
    round_fits,
    rounds_fit,
)


class _Rag:
    """Returns a distinct chunk per query, so every round is productive."""

    def __init__(self):
        self.n = 0

    def search(self, query, top_k=3):
        self.n += 1
        return [{"source_uri": f"euaiact://Article_{self.n}", "text": f"t{self.n}",
                 "score": 0.9}]


class _StaleRag:
    """Returns the same chunk every time — retrieval that teaches nothing."""

    def __init__(self):
        self.n = 0

    def search(self, query, top_k=3):
        self.n += 1
        return [{"source_uri": "euaiact://Article_10", "text": "same", "score": 0.9}]


class _Answerer:
    """Plans once, then answers — the common shape, and the one the gates save."""

    name = "Answerer"

    def __init__(self, sleep: float = 0.0):
        self.calls = 0
        self.sleep = sleep

    async def acompletion_json(self, prompt_name, payload):
        self.calls += 1
        if self.sleep:
            time.sleep(self.sleep)
        if self.calls == 1:
            return {"retrieval_plan": {"regulatory_queries": ["q"],
                                       "client_doc_queries": []}}
        return {"done": True}


class _Planner:
    """Keeps asking for more evidence until told the round is final, then answers.

    A compliant model, in other words: :data:`TERMINAL_NOTICE` says answer from
    what you have, and this one does. An agent that planned unconditionally
    would trip F15's closing re-prompt and measure that instead of the budget.
    """

    name = "Planner"

    def __init__(self, sleep: float = 0.0):
        self.calls = 0
        self.sleep = sleep
        self.seen: list[dict] = []

    async def acompletion_json(self, prompt_name, payload):
        self.calls += 1
        self.seen.append(payload)
        if self.sleep:
            time.sleep(self.sleep)
        if (payload.get("retrieval_expansion") or {}).get("final_round"):
            return {"done": True}
        return {"retrieval_plan": {"regulatory_queries": [f"q{self.calls}"],
                                   "client_doc_queries": []},
                "done": True}


def _run(agent, rag, **kw):
    """Drive the loop with a seeded hit already in the payload."""
    return asyncio.run(acompletion_json_react(
        agent, "p", {"regulatory_hits": [{"source_uri": "euaiact://Article_0",
                                          "text": "seed", "score": 1.0}]},
        rag=rag, engagement_id="", **kw))


# --------------------------------------------------------------------------- #
# the budget itself
# --------------------------------------------------------------------------- #

def test_no_binding_means_no_deadline():
    """A unit test or a direct dispatch has no budget to respect."""
    assert remaining_seconds() is None


def test_a_bound_budget_counts_down():
    with bind_phase_deadline(180):
        left = remaining_seconds()
    assert left is not None and 179.0 < left <= 180.0


def test_an_absent_budget_does_not_clear_the_one_around_it():
    """Narrowing never clearing — the rule `bind_engagement_id` follows."""
    with bind_phase_deadline(180):
        with bind_phase_deadline(None):
            assert remaining_seconds() is not None
        with bind_phase_deadline(0):
            assert remaining_seconds() is not None


def test_the_binding_is_released_again():
    with bind_phase_deadline(180):
        pass
    assert remaining_seconds() is None


# --------------------------------------------------------------------------- #
# gate one: can another round finish?
# --------------------------------------------------------------------------- #

def _left(monkeypatch, seconds: float | None) -> None:
    """Pin the budget remaining, so the real numbers can be stated exactly."""
    monkeypatch.setattr(rounds_mod, "remaining_seconds", lambda: seconds)


def test_a_round_is_allowed_when_the_budget_covers_the_slowest_call_so_far(monkeypatch):
    _left(monkeypatch, 144.6)
    assert round_fits([35.4]) is True


def test_a_round_is_refused_when_it_would_overrun_the_budget(monkeypatch):
    """P3's rerun, exactly: 71 s of a 180 s budget left after a 106.3 s call."""
    _left(monkeypatch, 71.0)
    assert round_fits([106.3]) is False


def test_the_estimate_is_the_slowest_call_not_the_last_or_the_mean(monkeypatch):
    """A cheap call after an expensive one must not license another expensive one."""
    _left(monkeypatch, 50.0)
    assert round_fits([95.0, 1.0]) is False        # max 95.0 > 50.0
    assert sum([95.0, 1.0]) / 2 < 50.0             # the mean would have allowed it


def test_an_already_spent_budget_refuses(monkeypatch):
    _left(monkeypatch, -4.8)
    assert round_fits([52.1]) is False


def test_without_a_measurement_the_gate_does_not_guess(monkeypatch):
    _left(monkeypatch, 1.0)
    assert round_fits([]) is True


def test_without_a_deadline_the_gate_never_refuses():
    assert round_fits([9999.0]) is True


def test_the_final_flag_looks_one_round_further_than_the_gate(monkeypatch):
    """It is stamped *before* the call it describes, so the open question is
    not "can this round run" — that is already settled — but "can another
    follow it". Answering the first question here told the model more
    retrieval was coming and then ran none."""
    _left(monkeypatch, 35.0)
    assert round_fits([20.0]) is True             # this round fits
    assert rounds_fit([20.0], 2) is False         # a second one does not
    assert is_final_round(1, 2, [20.0]) is True   # so round 1 is final


def test_the_ceiling_still_marks_the_last_round_final(monkeypatch):
    _left(monkeypatch, 9999.0)
    assert is_final_round(2, 2, [20.0]) is True
    assert is_final_round(1, 2, [20.0]) is False


# --------------------------------------------------------------------------- #
# gate two: did the round pay for itself?
# --------------------------------------------------------------------------- #

def test_a_round_that_returns_only_chunks_already_held_stops_the_loop():
    assert learned_something({("u", 0, "t")}, {("u", 0, "t")}) is False


def test_one_new_chunk_is_enough_to_continue():
    assert learned_something({("u", 0, "t")}, {("u", 0, "t"), ("v", 0, "t2")}) is True


def test_identity_not_length_decides():
    """At the cap a round can displace a weaker hit without growing the list."""
    before = {("u", 0, "t")}
    after = {("v", 0, "t2")}
    assert len(before) == len(after)
    assert learned_something(before, after) is True


def test_hit_keys_uses_the_key_merge_hits_de_duplicates_by():
    hits = [{"source_uri": "u", "chunk_index": 0, "text": "a"},
            {"source_uri": "u", "chunk_index": 0, "text": "a"},
            {"source_uri": "u", "chunk_index": 1, "text": "b"}]
    assert len(hit_keys(hits)) == 2


# --------------------------------------------------------------------------- #
# the loop
# --------------------------------------------------------------------------- #

def test_the_ceiling_is_two_rounds():
    """The whole of the raise: a missed retrieval now gets a second chance."""
    assert MAX_ROUNDS == 2


def test_a_productive_phase_with_time_to_spare_runs_both_rounds():
    agent = _Planner()
    _run(agent, _Rag())
    assert agent.calls == 3  # initial + two expansions


def test_a_phase_out_of_budget_stops_early_and_still_answers():
    """The point of the gate: a report on the evidence in hand beats no report."""
    agent = _Planner(sleep=0.20)
    with bind_phase_deadline(0.30):
        result = _run(agent, _Rag())
    assert agent.calls == 2  # initial + one expansion, second refused
    assert result["done"] is True


def test_retrieval_that_teaches_nothing_stops_the_loop():
    """Round 1 is productive; round 2 re-reads it and is not put to the model.

    The gate necessarily runs the queries before it can know they were stale —
    that is a vector search costing milliseconds. What it saves is the LLM call
    they would have been injected into, which cost 52.1 s at the run's median.
    """
    agent, rag = _Planner(), _StaleRag()
    _run(agent, rag)
    assert rag.n == 2                       # both rounds' queries were issued
    expansions = [p for p in agent.seen
                  if (p.get("retrieval_expansion") or {}).get("round")]
    assert len(expansions) == 1             # only the productive one reached the model


def test_a_phase_that_answers_pays_nothing_for_a_refused_round():
    """The gates save a whole round when the model has already answered."""
    agent = _Answerer(sleep=0.20)
    with bind_phase_deadline(0.30):
        _run(agent, _Rag())
    assert agent.calls == 2  # initial + the one expansion; no third call at all


def test_the_round_the_budget_makes_last_is_the_one_marked_final():
    """A model cannot be held to a deadline it was never given (fix 4's rule).

    Round 1 is *not* the ceiling here — the ceiling is 2 — so a `final_round`
    computed as ``round_idx == last`` would have told the model it had another
    round coming, and then not run one. The budget has to be what marks it.
    """
    agent = _Planner(sleep=0.20)
    with bind_phase_deadline(0.55):
        _run(agent, _Rag())
    expansions = [p["retrieval_expansion"] for p in agent.seen
                  if (p.get("retrieval_expansion") or {}).get("round")]
    assert len(expansions) == 1                  # the budget stopped it at round 1
    assert expansions[0]["round"] == 1
    assert expansions[0]["round"] != MAX_ROUNDS  # so the ceiling did not mark it
    assert expansions[0]["final_round"] is True
    assert "FINAL ROUND" in expansions[0]["notice"]


def test_a_phase_with_room_is_not_told_its_first_round_is_final():
    agent = _Planner()
    _run(agent, _Rag())
    assert agent.seen[1]["retrieval_expansion"]["final_round"] is False
    assert agent.seen[2]["retrieval_expansion"]["final_round"] is True


def test_phase_six_still_has_no_retrieval_channel():
    """`rounds=0` is a deliberate exception, not an oversight to be defaulted away."""
    agent = _Planner()
    _run(agent, _Rag(), rounds=0)
    assert agent.calls == 2  # the single shot, plus F15's closing re-prompt


# --------------------------------------------------------------------------- #
# wiring
# --------------------------------------------------------------------------- #

def test_no_phase_agent_pins_its_own_round_budget():
    """Five agents each passing the same literal is a policy fixed in five places."""
    agents = ["scope_agent", "data_auditor", "model_validator", "output_fairness",
              "governance_agent"]
    for name in agents:
        src = pathlib.Path(f"aaa/agents/tier2/{name}/llm.py").read_text(encoding="utf-8")
        assert "rounds=" not in src, name


def test_the_deadline_is_bound_only_where_the_timeout_is_enforced():
    """Two of `_invoke`'s three paths apply no timeout; a loop told otherwise
    would cut itself short against a limit nothing was going to apply."""
    src = pathlib.Path(
        "aaa/agents/tier1/phases/agent_runner/logger.py").read_text(encoding="utf-8")
    assert src.count("bind_phase_deadline(timeout)") == 1
    enforced = src.index("run_coro_blocking(agent.process(dispatch), timeout=timeout)")
    assert src.index("bind_phase_deadline(timeout)") < enforced
