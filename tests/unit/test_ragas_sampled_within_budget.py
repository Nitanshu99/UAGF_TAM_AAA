"""T-20260914-017: RAGAs is measured on as many seeded-random samples as the budget allows.

Case 04's 360 judge jobs cannot finish in the L-branch budget on the free route; an
all-or-nothing evaluation reported nothing, and on a paid route discarded what it bought.
"""
from __future__ import annotations

import asyncio

from aaa.agents.tier3.uagf_tam_l.ragas_verdict import target_notes
from aaa.tools.ragas_eval.compute import batches
from aaa.tools.ragas_eval.compute.sampled import aggregate, sample_order


def _fake_evaluate(delays: list[float], seen: list[list[str]]):
    """A judge whose n-th batch takes delays[n] seconds and scores every sample 0.8."""
    async def evaluate(questions, _contexts, _answers, _references, budget_s):
        delay = delays[len(seen)]
        seen.append(list(questions))
        if budget_s is not None and delay > budget_s:
            raise asyncio.TimeoutError
        await asyncio.sleep(delay)
        return {"faithfulness": [0.8] * len(questions)}, {"faithfulness": "faithfulness"}
    return evaluate


def test_batches_stop_before_one_the_budget_cannot_cover_and_keep_the_rest(monkeypatch) -> None:
    """Two 0.3 s batches fit a 0.7 s budget; a third is not started."""
    seen: list[list[str]] = []
    monkeypatch.setattr(batches, "_aevaluate", _fake_evaluate([0.3, 0.3, 0.3, 0.3], seen))
    rows = ([f"q{i}" for i in range(20)], [["c"]] * 20, ["a"] * 20, None)
    per_metric, measured, _spent = asyncio.run(batches._measure(rows, 0.7, 5))
    assert measured == 10 and len(seen) == 2 and per_metric["faithfulness"] == [0.8] * 10
    assert seen[0] == [f"q{i}" for i in sample_order(20)[:5]]


def test_aggregate_reports_the_sample_and_its_interval() -> None:
    """Mean, interval, sample and population sizes, and a reason saying it was a sample."""
    out = aggregate({"faithfulness": [0.7, 0.9] * 5}, 10, 55, ("faithfulness", "answer_relevance"))
    assert out["faithfulness"] == 0.8 and out["answer_relevance"] is None
    low, high = out["intervals"]["faithfulness"]
    assert low < 0.8 < high and out["sample_size"] == 10 and out["population_size"] == 55
    assert "10 of 55 samples" in out["reason"]


def test_a_target_is_missed_only_when_the_interval_lies_below_it() -> None:
    """Below → fail; straddling → not established; above → nothing to say."""
    declared = {"ragas_faithfulness_target": 0.9}

    def ragas(low: float, high: float) -> dict:
        return {"faithfulness": (low + high) / 2, "intervals": {"faithfulness": [low, high]},
                "sample_size": 10, "population_size": 55}

    assert target_notes(ragas(0.70, 0.85), declared)[1] is True
    notes, failed = target_notes(ragas(0.85, 0.95), declared)
    assert not failed and "not established" in notes[0]
    assert target_notes(ragas(0.92, 0.98), declared) == ([], False)
