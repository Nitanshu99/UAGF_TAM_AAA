"""Part 4 of the former ``toxicity_classifier`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.toxicity_classifier.compute.detoxify import _compute_detoxify  # noqa: F401
from aaa.tools.toxicity_classifier.compute.python import (  # noqa: F401
    _compute_python,
    _empty_result,
)
from aaa.tools.toxicity_classifier.logger import (  # noqa: F401
    _DEFAULT_SAMPLE_SIZE,
    _DEFAULT_THRESHOLD,
    _DISCRIMINATORY_KEYWORDS,
    _DISCRIMINATORY_RE,
    _assemble,
    logger,
)


def toxicity_classifier(
    predictions: Sequence[Any] | None = None,
    prediction_ids: Sequence[Any] | None = None,
    sample_size: int = _DEFAULT_SAMPLE_SIZE,
    threshold: float = _DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """
    Score up to ``sample_size`` predictions for toxicity / discriminatory content.

    Parameters
    ----------
    predictions:
        Iterable of model outputs (strings expected).  Non-string entries
        are coerced via ``str``.  Empty / None → empty-result stub.
    prediction_ids:
        Optional iterable of identifiers for traceability in T13.
    sample_size:
        Cap on number of predictions scored (default 200, per §4A T13).
    threshold:
        Probability threshold above which a prediction is flagged.

    Returns
    -------
    dict matching the T13 ``toxicity_results`` sub-schema:
        {
            sample_size, flagged_count, flagged_pct,
            entries[], categories_observed[], verdict,
            tool, threshold
        }
    """
    if not predictions:
        return _empty_result()

    capped = list(predictions)[:max(0, sample_size)]
    ids = list(prediction_ids)[:len(capped)] if prediction_ids else list(range(len(capped)))
    if len(ids) < len(capped):
        ids.extend(range(len(ids), len(capped)))

    try:
        return _compute_detoxify(capped, ids, threshold)
    except Exception as exc:
        logger.info("detoxify unavailable (%s); using keyword fallback.", exc)
        return _compute_python(capped, ids)
