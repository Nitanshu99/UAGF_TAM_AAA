"""Metric selection for the RAGAs 0.4 API.

ragas 0.4 removed the pre-instantiated ``ragas.metrics.faithfulness`` style
singletons; metrics are now classes that must be instantiated, and the result
keys are the class ``name`` attributes rather than the T16 field names. This
module owns both the instantiation and the name translation so
:mod:`aaa.tools.ragas_eval.compute.ragas` stays a thin driver.

Three of the six T16 metrics (``answer_similarity``, ``answer_correctness``,
``context_recall``) score an answer against a ground-truth reference and are
only requested when the caller supplies one — the golden set's ``expected``
column. Without it they are reported as not computed rather than guessed.
"""
from __future__ import annotations

from typing import Any

#: T16 field name -> ragas 0.4 result key, for the reference-free metrics.
_BASE_KEYS = {
    "faithfulness": "faithfulness",
    "answer_relevance": "answer_relevancy",
    "context_precision": "llm_context_precision_without_reference",
}

#: T16 field name -> ragas 0.4 result key, for the reference-scored metrics.
_REFERENCE_KEYS = {
    "context_precision": "llm_context_precision_with_reference",
    "context_recall": "context_recall",
    "answer_similarity": "answer_similarity",
    "answer_correctness": "answer_correctness",
}


def build_metrics(with_reference: bool) -> tuple[list[Any], dict[str, str]]:
    """Instantiate the ragas metrics and the T16 field -> result-key map.

    :param with_reference: Whether the caller supplied ground-truth references.
        When ``True`` all six T16 metrics are requested; when ``False`` only
        the three that score without a reference.
    :type with_reference: bool
    :returns: ``(metric_instances, {t16_field: ragas_result_key})``.
    :rtype: tuple[list[Any], dict[str, str]]
    """
    from ragas.metrics._answer_correctness import AnswerCorrectness
    from ragas.metrics._answer_relevance import AnswerRelevancy
    from ragas.metrics._answer_similarity import AnswerSimilarity
    from ragas.metrics._context_precision import (
        LLMContextPrecisionWithoutReference,
        LLMContextPrecisionWithReference,
    )
    from ragas.metrics._context_recall import LLMContextRecall
    from ragas.metrics._faithfulness import Faithfulness

    metrics: list[Any] = [Faithfulness(), AnswerRelevancy()]
    keys = dict(_BASE_KEYS)
    if with_reference:
        metrics += [LLMContextPrecisionWithReference(), LLMContextRecall(),
                    AnswerSimilarity(), AnswerCorrectness()]
        keys.update(_REFERENCE_KEYS)
    else:
        metrics.append(LLMContextPrecisionWithoutReference())
    return metrics, keys
