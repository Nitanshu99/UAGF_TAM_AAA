"""Part 2 of the former ``evidence_truncate`` module (auto-split)."""
from __future__ import annotations

import hashlib
from typing import Any

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


def _dense_scores(query: str, texts: list[str]) -> list[float] | None:
    """Cosine-rank *texts* against *query* using the evidence embedder.

    Returns ``None`` when embeddings are unavailable so the caller falls back
    to the lexical scorer. The key check is the provider's own: a local model
    needs none, OpenAI and OpenRouter each need theirs.

    :param query: Ranking query.
    :type query: str
    :param texts: Candidate texts.
    :type texts: list[str]
    :returns: One score per text, or ``None`` to fall back.
    :rtype: list[float] | None
    """
    from aaa.platform.embeddings import credentials_present, embed_texts

    try:
        if not credentials_present("evidence"):
            return None
        vectors = embed_texts([query] + texts, "evidence")
        return [_cosine(vectors[0], v) for v in vectors[1:]]
    except Exception as exc:  # noqa: BLE001
        logger.info("dense embedder unavailable (%s); using lexical scorer.", exc)
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
