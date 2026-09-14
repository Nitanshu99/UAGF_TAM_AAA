"""Real RAGAs computation against the ragas 0.4 evaluation API.

ragas 0.4 replaced the HuggingFace ``Dataset`` input with
``EvaluationDataset``/``SingleTurnSample`` and renamed the columns
(``question`` -> ``user_input``, ``contexts`` -> ``retrieved_contexts``,
``answer`` -> ``response``). Metric selection and result-key translation live
in :mod:`aaa.tools.ragas_eval.compute.metrics`.
"""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.ragas_eval.compute.judge import build_judge
from aaa.tools.ragas_eval.compute.metrics import build_metrics
from aaa.tools.ragas_eval.compute.run_config import run_config
from aaa.tools.ragas_eval.compute.samples import _samples, _score
from aaa.tools.ragas_eval.logger import logger  # noqa: F401

#: The T16 ``ragas_metrics`` scores, whether or not this run requests each one.
FIELDS = ("faithfulness", "answer_relevance", "context_precision",
          "context_recall", "answer_similarity", "answer_correctness")


def _prepare(questions: Sequence[str], contexts: Sequence[Sequence[str]],
             answers: Sequence[str], references: Sequence[str] | None) -> dict[str, Any]:
    """The ``evaluate`` keyword arguments and the result keys to read back."""
    from ragas import EvaluationDataset

    metrics, keys = build_metrics(references is not None)
    llm, embeddings = build_judge()
    dataset = EvaluationDataset(samples=_samples(questions, contexts, answers, references))
    return {"kwargs": {"dataset": dataset, "metrics": metrics, "llm": llm,
                       "embeddings": embeddings, "run_config": run_config()}, "keys": keys}


def _scores(result: Any, keys: dict[str, str], references: Sequence[str] | None) -> dict[str, Any]:
    """T16 ``ragas_metrics`` from an ``EvaluationResult``."""
    scores: dict[str, Any] = {field: _score(result, key) for field, key in keys.items()}
    for field in FIELDS:
        scores.setdefault(field, None)
    scores["computed"] = True
    scores["reason"] = (
        "" if references is not None
        else "no reference answers supplied; reference-scored metrics skipped")
    return scores


def _compute_ragas(
    questions: Sequence[str],
    contexts: Sequence[Sequence[str]],
    answers: Sequence[str],
    references: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Use the real ragas library.

    :param references: Ground-truth answers (the golden set's ``expected``
        column). When ``None`` the three reference-scored metrics are reported
        as ``None`` instead of being requested.
    :returns: T16 ``ragas_metrics`` shape with ``computed: True``.
    :rtype: dict[str, Any]
    """
    from ragas import evaluate

    prepared = _prepare(questions, contexts, answers, references)
    return _scores(evaluate(**prepared["kwargs"]), prepared["keys"], references)
