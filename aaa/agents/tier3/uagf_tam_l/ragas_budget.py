"""How long the L-branch lets its RAGAs evaluation run (T-20260914-013)."""
from __future__ import annotations

from typing import Any

from aaa.tools.ragas_eval import aragas_eval


def ragas_budget(agent: Any) -> float | None:
    """Seconds the RAGAs evaluation may take: the phase's remainder, less the branch's
    slowest recent call, which its closing synthesis still has to make."""
    from aaa.platform.phase_budget import remaining_seconds, slowest_call

    remaining = remaining_seconds()
    if remaining is None:
        return None
    return remaining - (slowest_call(getattr(agent, "name", None)) or 0.0)


async def bounded_ragas(agent: Any, questions: list, contexts: list, answers: list,
                        expected: list) -> dict[str, Any]:
    """The branch's RAGAs metrics, measured within :func:`ragas_budget`."""
    return await aragas_eval(questions, contexts, answers, expected, ragas_budget(agent))


__all__ = ["bounded_ragas", "ragas_budget"]
