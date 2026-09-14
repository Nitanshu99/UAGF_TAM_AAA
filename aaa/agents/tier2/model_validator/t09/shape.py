"""The model's output shape, where the provider's documents state it."""
from __future__ import annotations

import re
from typing import Mapping

from aaa.tools.document_evidence import Evidence

_DIMENSIONS = re.compile(r"(\d[\d,]*)\s*-?\s*dimension(?:al|s)?", re.IGNORECASE)


def output_shape(found: Mapping[str, Evidence | None]) -> str | None:
    """"128-dimensional vector (model_card.md)" from a grounded passage, else ``None``.

    :param found: Grounded answers to the T09 questions.
    """
    evidence = found.get("output_shape")
    size = _DIMENSIONS.search(evidence.quote) if evidence else None
    if not evidence or not size:
        return None
    return f"{size.group(1).replace(',', '')}-dimensional vector ({evidence.origin})"


__all__ = ["output_shape"]
