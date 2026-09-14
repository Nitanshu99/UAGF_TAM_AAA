"""RAGAs metric computation with an explicit not-computed fallback.

When the ragas library is unavailable the tool reports ``computed: False``
with null metrics — it never invents scores. An earlier version returned six
``random.uniform`` values as a "mock", which are indistinguishable from
measurements once they reach a T16 artefact.
"""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.ragas_eval.compute.ragas import _compute_ragas  # noqa: F401
from aaa.tools.ragas_eval.logger import logger  # noqa: F401


def _not_computed(reason: str) -> dict[str, Any]:
    """Build the explicit not-computed RAGAs result.

    :param reason: Why the metrics could not be measured.
    :type reason: str
    :returns: T16 ``ragas_metrics`` shape with null metrics.
    :rtype: dict[str, Any]
    """
    return {
        "computed": False,
        "reason": reason,
        "faithfulness": None,
        "answer_relevance": None,
        "context_precision": None,
        "context_recall": None,
        "answer_similarity": None,
        "answer_correctness": None,
    }


def input_gap(questions: list, contexts: list, answers: list) -> str | None:
    """Why these inputs cannot be scored, or ``None`` when they can."""
    if not questions or not any(str(a).strip() for a in answers):
        return ("no system answers were supplied, so answer quality could not be "
                "measured; the questions and references were read")
    if not any(c for c in contexts):
        return ("no retrieved context was supplied, so faithfulness, context "
                "precision and context recall could not be measured")
    return None


def ragas_eval(
    questions: Sequence[str] | None = None,
    contexts: Sequence[Sequence[str]] | None = None,
    answers: Sequence[str] | None = None,
    references: Sequence[str] | None = None,
) -> dict[str, Any]:
    """
    Compute RAGAs metrics (faithfulness, answer_relevance, etc.).

    Parameters
    ----------
    questions:
        List of input queries.
    contexts:
        List of context snippets retrieved for each question.
    answers:
        List of generated answers.
    references:
        Ground-truth answers (the golden set's ``expected`` column). Required
        for ``answer_similarity``, ``answer_correctness`` and
        ``context_recall``; when omitted those three are reported as ``None``
        and the remaining three are still measured.

    Returns
    -------
    dict matching the T16 ``ragas_metrics`` sub-schema.
    """
    # A list of empty strings is not input. RAGAs will happily score `""`
    # against a reference and return `answer_correctness: 0.032` with
    # `computed: true`, which is a measurement of nothing presented as a
    # measurement of the client's system — and 3.2 % reads as catastrophic.
    # A golden set exported before the system was run against it has exactly
    # this shape: real questions, real references, no answers.
    questions, contexts, answers = list(questions or []), list(contexts or []), list(answers or [])
    gap = input_gap(questions, contexts, answers)
    if gap:
        return _not_computed(gap)

    try:
        return _compute_ragas(questions, contexts, answers, references or None)
    except Exception as exc:  # noqa: BLE001 — reported, never faked
        logger.info("ragas unavailable (%s); reporting not computed.", exc)
        return _not_computed(f"ragas unavailable ({type(exc).__name__})")
