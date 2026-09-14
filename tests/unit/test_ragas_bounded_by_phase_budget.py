"""T-20260914-013: the RAGAs evaluation stops at the L-branch's deadline instead of outliving it.

Case 04's 360-job evaluation ran on for twelve minutes after the branch was abandoned
at its 300 s budget, calling the free judge for a phase nobody was waiting on.
"""
from __future__ import annotations

import asyncio

import pytest

from aaa.agents.tier3.uagf_tam_l.ragas_budget import ragas_budget
from aaa.platform.phase_budget import bind_phase_deadline, observe, reset
from aaa.tools.ragas_eval import aragas_eval

ragas = pytest.importorskip("ragas")


def _slow_evaluation(monkeypatch, calls: list[int]) -> None:
    """Replace the judge with one that takes a second per call and counts them."""
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from ragas import EvaluationDataset, SingleTurnSample
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness  # pylint: disable=no-name-in-module

    class _Slow(FakeListChatModel):
        async def _agenerate(self, *args, **kwargs):
            calls.append(1)
            await asyncio.sleep(1.0)
            return await super()._agenerate(*args, **kwargs)

    samples = [SingleTurnSample(user_input=f"q{i}", response="a", retrieved_contexts=["c"])
               for i in range(40)]
    prepared = {"kwargs": {"dataset": EvaluationDataset(samples=list(samples)),  # type: ignore[arg-type]
                           "metrics": [Faithfulness()],
                           "llm": LangchainLLMWrapper(_Slow(responses=["{}"] * 1000))},
                "keys": {"faithfulness": "faithfulness"}}
    monkeypatch.setattr("aaa.tools.ragas_eval.compute.batches._prepare", lambda *a: prepared)


def test_an_evaluation_past_its_budget_is_cancelled_and_says_so(monkeypatch) -> None:
    """Not computed, with the reason, and no judge call starts after the deadline."""
    calls: list[int] = []
    _slow_evaluation(monkeypatch, calls)

    async def run() -> tuple[dict, int]:
        result = await aragas_eval(["q"] * 40, [["c"]] * 40, ["a"] * 40, None, 1.5)
        started = len(calls)
        await asyncio.sleep(2.0)
        return result, len(calls) - started

    result, after = asyncio.run(run())
    assert result["computed"] is False and "was cancelled" in result["reason"]
    assert after == 0


def test_no_time_left_measures_nothing_and_the_budget_reserves_the_synthesis() -> None:
    """A spent budget is not computed; the reserve is the branch's slowest call."""
    assert asyncio.run(aragas_eval(["q"], [["c"]], ["a"], None, 0.0))["computed"] is False
    reset()
    with bind_phase_deadline(300):
        observe("UAGF-TAM-L", 120.0)
        agent = type("Agent", (), {"name": "UAGF-TAM-L"})()
        budget = ragas_budget(agent)
    assert budget is not None and 170 < budget <= 180
    reset()
