"""The RAGAs evaluation within a phase's budget, cancelled rather than abandoned.

On the free judge route case 04's 360 evaluation jobs ran ~4 s each. The synchronous
``ragas.evaluate`` could not be interrupted by the phase deadline: the L-branch was
abandoned at 300 s with no report while the evaluation kept calling the judge for
another twelve minutes (T-20260914-013). Awaited here, it stops when the time is up.
"""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.ragas_eval.compute.batches import _measure
from aaa.tools.ragas_eval.compute.mock import _not_computed, input_gap
from aaa.tools.ragas_eval.compute.ragas import FIELDS
from aaa.tools.ragas_eval.compute.run_config import run_config
from aaa.tools.ragas_eval.compute.sampled import aggregate
from aaa.tools.ragas_eval.logger import logger


async def aragas_eval(questions: Sequence[str], contexts: Sequence[Sequence[str]],
                      answers: Sequence[str], references: Sequence[str] | None,
                      budget_s: float | None) -> dict[str, Any]:
    """RAGAs metrics on as many seeded-random samples as *budget_s* allows, or why not.

    :param budget_s: Seconds the evaluation may take; ``None`` for no bound.
    :returns: T16 ``ragas_metrics``, with the sample size and intervals.
    """
    rows = (list(questions), list(contexts), list(answers), list(references or []) or None)
    gap = input_gap(rows[0], rows[1], rows[2])
    if gap:
        return _not_computed(gap)
    if budget_s is not None and budget_s <= 0:
        return _not_computed("the phase had no time left for the RAGAs evaluation")
    try:
        per_metric, measured, spent = await _measure(rows, budget_s, run_config().max_workers)
    except Exception as exc:  # noqa: BLE001 — reported, never faked
        logger.info("ragas unavailable (%s); reporting not computed.", exc)
        return _not_computed(f"ragas unavailable ({type(exc).__name__})")
    if not measured:
        return _not_computed(f"no batch of the {len(rows[0])}-sample RAGAs evaluation finished in "
                             f"the {spent:.0f} s the phase had left, and the unfinished one was cancelled")
    return aggregate(per_metric, measured, len(rows[0]), FIELDS)


__all__ = ["aragas_eval"]
