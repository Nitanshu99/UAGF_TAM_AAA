"""Part 3 of the former ``evidence_truncate`` module (auto-split)."""
from __future__ import annotations

from typing import Any, Iterable

from aaa.platform.token_guard import count_tokens
from aaa.tools.evidence_truncate.dense_scores import _dense_scores, _rank_keys  # noqa: F401
from aaa.tools.evidence_truncate.logger import (  # noqa: F401
    _DENSE_MODEL,
    _WORD_RE,
    TruncationResult,
    _cosine,
    _jaccard,
    _serialise,
    _tokens,
    logger,
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
