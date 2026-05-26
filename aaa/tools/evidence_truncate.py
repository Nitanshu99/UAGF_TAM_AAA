"""
evidence_truncate — deterministic prompt-payload compressor (§8.1).

When :class:`aaa.platform.token_guard.ensure_within_budget` rejects an
oversized prompt, the caller can route the artefact payload through this
tool to drop the least-relevant top-level entries while always keeping
schema-required keys.

Ranking strategy (deterministic in both branches):

* **Dense branch** — when an OpenAI client + ``OPENAI_API_KEY`` are
  available *and* ``AAA_OFFLINE_MODE`` is not set: each top-level value is
  serialised, embedded with ``text-embedding-3-small`` (1536-dim), and
  ranked by cosine similarity against the query embedding.
* **Offline branch** — token-overlap (Jaccard on lowercased ASCII word
  tokens). Produces stable scores from the same inputs without network.

The function never mutates the input; it returns a new dict containing
``preserve_keys`` plus as many ranked keys as fit inside ``max_tokens``,
annotated with ``_truncated`` + ``_dropped_keys`` markers so the Verifier
records that compression occurred.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable

from aaa.platform.token_guard import count_tokens

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_DENSE_MODEL = "text-embedding-3-small"
_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class TruncationResult:
    """Outcome of an :func:`truncate_payload` call."""

    payload: dict[str, Any]
    kept_keys: list[str]
    dropped_keys: list[str]
    final_tokens: int

    def to_dict(self) -> dict[str, Any]:
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


def _dense_scores(query: str, texts: list[str]) -> list[float] | None:
    if _OFFLINE or not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        import openai  # type: ignore

        client = openai.OpenAI()
        resp = client.embeddings.create(model=_DENSE_MODEL, input=[query] + texts)
        qvec = list(resp.data[0].embedding)
        return [_cosine(qvec, list(item.embedding)) for item in resp.data[1:]]
    except Exception as exc:  # noqa: BLE001
        logger.info("OpenAI embedder unavailable (%s); using offline scorer.", exc)
        return None


def _rank_keys(
    payload: dict[str, Any], rankable: list[str], query: str
) -> list[tuple[str, float]]:
    texts = [_serialise(payload[k]) for k in rankable]
    scores = _dense_scores(query, texts)
    if scores is None:
        q_toks = _tokens(query)
        scores = [_jaccard(q_toks, _tokens(t)) for t in texts]

    def _stable_tiebreak(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    return sorted(
        zip(rankable, scores),
        key=lambda kv: (-kv[1], _stable_tiebreak(kv[0])),
    )


def truncate_payload(
    payload: dict[str, Any],
    query: str,
    *,
    model: str,
    max_tokens: int,
    preserve_keys: Iterable[str] | None = None,
) -> TruncationResult:
    """Compress *payload* so its JSON serialisation fits in ``max_tokens``.

    ``preserve_keys`` are kept unconditionally even when over budget; the
    remainder is ranked by relevance to *query* and added until the next
    entry would breach the limit.
    """
    if not isinstance(payload, dict):
        raise TypeError("evidence_truncate expects a dict payload")

    preserve = [k for k in (preserve_keys or []) if k in payload]
    base = {k: payload[k] for k in preserve}
    base_tokens = count_tokens(model, text=_serialise(base))

    rankable = [k for k in payload.keys() if k not in preserve]
    ranked = _rank_keys(payload, rankable, query)

    out = dict(base)
    used = base_tokens
    kept: list[str] = list(preserve)
    dropped: list[str] = []
    for key, _score in ranked:
        candidate = dict(out)
        candidate[key] = payload[key]
        new_tokens = count_tokens(model, text=_serialise(candidate))
        if new_tokens > max_tokens:
            dropped.append(key)
            continue
        out = candidate
        used = new_tokens
        kept.append(key)

    return TruncationResult(
        payload=out, kept_keys=kept, dropped_keys=dropped, final_tokens=used
    )


__all__ = ["TruncationResult", "truncate_payload"]
