"""Part 1 of the former ``evidence_truncate`` module (auto-split)."""
from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


_DENSE_MODEL = "text-embedding-3-large"


_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class TruncationResult:
    """Outcome of an :func:`truncate_payload` call."""

    payload: dict[str, Any]
    kept_keys: list[str]
    dropped_keys: list[str]
    final_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Return the TruncationResult as a plain dict."""
        out = dict(self.payload)
        if self.dropped_keys:
            out["_truncated"] = True
            out["_dropped_keys"] = list(self.dropped_keys)
        return out


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _serialise(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(value)


def _cosine(u: list[float], v: list[float]) -> float:
    nu = math.sqrt(sum(x * x for x in u)) or 1.0
    nv = math.sqrt(sum(x * x for x in v)) or 1.0
    return sum(x * y for x, y in zip(u, v)) / (nu * nv)
