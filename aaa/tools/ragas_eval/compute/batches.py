"""Evaluating golden-set batches one at a time, each cancelled at the deadline."""
from __future__ import annotations

import asyncio
import time
from typing import Any

from aaa.tools.ragas_eval.compute.ragas import _prepare
from aaa.tools.ragas_eval.compute.sampled import finite, sample_order


async def _aevaluate(questions: list, contexts: list, answers: list,
                    references: list | None, budget_s: float | None) -> tuple[Any, dict]:
    """``(EvaluationResult, result keys)`` for these samples, cancelled after *budget_s*.

    :raises asyncio.TimeoutError: When the evaluation did not finish in time; its
        outstanding judge calls are cancelled with it.
    """
    from ragas.evaluation import aevaluate

    prepared = _prepare(questions, contexts, answers, references)
    before = set(asyncio.all_tasks())
    try:
        result = await asyncio.wait_for(
            aevaluate(**prepared["kwargs"], show_progress=False), budget_s)
    except asyncio.TimeoutError:
        # ragas starts one task per job up front and cancels them only while its own
        # iterator is being read; a cancelled reader leaves every queued job running.
        started = [t for t in asyncio.all_tasks() - before if not t.done()]
        for task in started:
            task.cancel()
        await asyncio.gather(*started, return_exceptions=True)
        raise
    return result, prepared["keys"]


async def _measure(rows: tuple[list, list, list, list | None], budget_s: float | None,
                   batch: int) -> tuple[dict[str, list[float]], int, float]:
    """Evaluate batches in seeded order until the next one would not fit the budget."""
    questions, contexts, answers, references = rows
    per_metric: dict[str, list[float]] = {}
    measured, slowest, started = 0, 0.0, time.monotonic()
    for offset in range(0, len(questions), batch):
        left = None if budget_s is None else budget_s - (time.monotonic() - started)
        if left is not None and (left <= 0 or left < slowest):
            break
        idx = sample_order(len(questions))[offset:offset + batch]
        t0 = time.monotonic()
        try:
            result, keys = await _aevaluate(
                [questions[i] for i in idx], [contexts[i] for i in idx], [answers[i] for i in idx],
                None if references is None else [references[i] for i in idx], left)
        except asyncio.TimeoutError:
            break
        slowest = max(slowest, time.monotonic() - t0)
        for field, key in keys.items():
            per_metric.setdefault(field, []).extend(finite(_value(result, key)))
        measured += len(idx)
    return per_metric, measured, time.monotonic() - started


def _value(result: Any, key: str) -> Any:
    """The per-row scores of one metric, or nothing when ragas has none."""
    try:
        return result[key]
    except (KeyError, TypeError, IndexError):
        return []


__all__ = ["_aevaluate", "_measure"]
