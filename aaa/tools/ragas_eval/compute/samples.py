"""Building the RAGAs sample set, and scoring one metric over it."""
from __future__ import annotations

from typing import Any, Sequence


def _samples(questions: Sequence[str], contexts: Sequence[Sequence[str]],
             answers: Sequence[str], references: Sequence[str] | None) -> list[Any]:
    """Build the aligned ``SingleTurnSample`` rows for ragas 0.4."""
    from ragas import SingleTurnSample

    rows = []
    for i, question in enumerate(questions):
        context = contexts[i] if i < len(contexts) else []
        fields: dict[str, Any] = {
            "user_input": str(question),
            "retrieved_contexts": [str(c) for c in context],
            "response": str(answers[i]) if i < len(answers) else "",
        }
        if references is not None and i < len(references):
            fields["reference"] = str(references[i])
        rows.append(SingleTurnSample(**fields))
    return rows
def _score(result: Any, key: str) -> float | None:
    """Mean one metric across the evaluated rows, or ``None`` if unscored.

    ``EvaluationResult[key]`` yields the *per-row* scores in ragas 0.4 (the
    aggregate is only exposed through ``__repr__``), so the mean is taken
    here. Rows ragas could not score come back as ``NaN`` and are dropped; if
    every row is ``NaN`` the metric is reported as not computed rather than
    as a zero.
    """
    try:
        value = result[key]
    except (KeyError, TypeError, IndexError):
        return None
    if value is None:
        return None
    values = value if isinstance(value, (list, tuple)) else [value]
    scored = [float(v) for v in values if v is not None and float(v) == float(v)]
    return sum(scored) / len(scored) if scored else None


__all__ = ["_samples", "_score"]
