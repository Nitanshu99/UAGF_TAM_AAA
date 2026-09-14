"""Cross-encoder re-ranking — judge relevance, hand the text over unedited.

**Why a second ranking at all.** RRF fuses two *bi-encoder* rankings: the query
and each chunk are embedded apart and compared by vector distance. That is fast
and recall-friendly and it never reads the two together, so it cannot tell that
"Article 10 data governance" and a Recital *about* data governance answer
different questions. Three chunks then survive out of the 64 the two branches
prefetched, with nothing having judged whether any of the three is on point —
the gap this module closes.

A cross-encoder reads ``(query, chunk)`` as one sequence and scores relevance
directly. It is a small local model (``fastembed`` already ships in this repo
for the BM25 sparse vectors), so this costs milliseconds and no network call —
which matters at the twenty-to-forty retrievals a run makes.

**Why not an LLM here, and why not a paraphrase anywhere.** Selection is the
job; rewriting is not. This module reorders and annotates the corpus hits and
never touches ``text``, so "verbatim" is structural rather than a promise a
model has to keep — an audit cites the law, and a retyped excerpt is a place a
citation can drift. An LLM filter would add one thing a cross-encoder cannot:
a *reason* for each rejection. That is worth having and is not built here.

**Why a threshold is defensible now, when fix 9 refused one.** Fix 9 declined
an absolute score floor because bi-encoder similarities are provider-scale
values — ``score >= 0.2`` means different things either side of an embedding
swap, and could silently empty the evidence channel. A cross-encoder trained on
binary relevance puts its decision boundary at **logit 0** by construction, so
:data:`RELEVANT_ABOVE` is a property of the model rather than a tuning
constant, and it does not move when the *embedding* provider does.

**Nothing is silently dropped.** Candidates that do not make ``top_k`` are
logged with their scores, so the trail shows what was considered and passed
over. Fix 1's lesson was that a retrieval which returns nothing must say so;
the same applies to one that returns less than it saw.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.regulatory_rag.rerank.encoder import MODEL_NAME, _get_encoder
from aaa.agents.tier1.regulatory_rag.rerank.scoring import RELEVANT_ABOVE, _annotate, _log_outcome

logger = logging.getLogger(__name__)

#: Candidates pulled from the corpus before re-ranking. Free at the Qdrant end
#: — ``_PREFETCH_LIMIT`` already fuses 32 per branch — and the pool is what buys
#: the recall: a passage ranked 4th by RRF used to be unreachable.
CANDIDATE_POOL = 15

def rerank(query: str, hits: list[dict[str, Any]], top_k: int,
           *, encoder: Any = None) -> list[dict[str, Any]]:
    """Re-rank *hits* against *query* and return the best ``top_k``, annotated.

    Never raises and never edits a chunk's ``text``: on any failure the RRF
    order is returned unchanged, because a critique or a phase report with
    unranked law is worse than one with none only if it does not happen.

    :param query: The question the hits were retrieved for.
    :type query: str
    :param hits: Candidate chunks, in retrieval order.
    :type hits: list[dict[str, Any]]
    :param top_k: How many to return.
    :type top_k: int
    :param encoder: Injected encoder (tests); the shared one when ``None``.
    :type encoder: Any
    :returns: Up to *top_k* hits, best first, each carrying its judgement.
    :rtype: list[dict[str, Any]]
    """
    if not hits or top_k <= 0:
        return []
    model = encoder if encoder is not None else _get_encoder()
    if model is None:
        return hits[:top_k]
    try:
        scores = [float(s) for s in model.rerank(query, [str(h.get("text") or "")
                                                         for h in hits])]
    except Exception as exc:  # noqa: BLE001 - never fail a phase over ranking
        logger.warning("Re-ranking failed for %r (%s); keeping RRF order.", query, exc)
        return hits[:top_k]

    order = sorted(zip(hits, scores), key=lambda pair: pair[1], reverse=True)
    kept = [_annotate(hit, logit, i) for i, (hit, logit) in enumerate(order[:top_k], 1)]
    _log_outcome(query, kept, order[top_k:])
    return kept


__all__ = ["CANDIDATE_POOL", "MODEL_NAME", "RELEVANT_ABOVE", "rerank"]
