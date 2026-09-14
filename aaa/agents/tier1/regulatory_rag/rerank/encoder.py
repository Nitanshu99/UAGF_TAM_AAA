"""The process-wide cross-encoder, loaded lazily and once."""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

#: Small, fast, English. Overridable for a multilingual corpus.
MODEL_NAME = os.environ.get("AAA_RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")

_ENCODER: Any = None
_UNAVAILABLE = False


def _get_encoder() -> Any:
    """Return the process-wide cross-encoder, or ``None`` if unavailable.

    Loaded lazily and once: the model is a few tens of MB and is fetched on
    first use, so importing this module must not pay for it. A failure is
    recorded so the import is attempted once rather than per query.

    :returns: The encoder, or ``None`` when re-ranking cannot run.
    :rtype: Any
    """
    global _ENCODER, _UNAVAILABLE  # pylint: disable=global-statement
    if _ENCODER is not None or _UNAVAILABLE:
        return _ENCODER
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _ENCODER = TextCrossEncoder(model_name=MODEL_NAME)
    except Exception as exc:  # noqa: BLE001 - retrieval must survive its absence
        _UNAVAILABLE = True
        logger.warning(
            "Cross-encoder re-ranking unavailable (%s); falling back to RRF order. "
            "Hits are still de-duplicated and score-ranked (fix 9), but nothing has "
            "judged whether the top chunk answers the query.", exc)
    return _ENCODER


__all__ = ["MODEL_NAME", "_get_encoder"]
