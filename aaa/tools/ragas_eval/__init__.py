"""ragas_eval — Faithfulness and answer-relevance metrics (§4.4).

Production path:  ragas (metrics.faithfulness, metrics.answer_relevance).
Fallback:         pure-Python mock when the ragas library is unavailable.

Usage
-----
    from src.tools.ragas_eval import ragas_eval
    metrics = ragas_eval(question, contexts, answer)"""
from aaa.tools.ragas_eval.compute.bounded import aragas_eval  # noqa: F401
from aaa.tools.ragas_eval.compute.mock import _not_computed, ragas_eval  # noqa: F401
from aaa.tools.ragas_eval.compute.ragas import _compute_ragas  # noqa: F401
from aaa.tools.ragas_eval.logger import logger  # noqa: F401

__all__ = [
    'logger',
    '_compute_ragas',
    '_not_computed',
    'aragas_eval',
    'ragas_eval',
]
