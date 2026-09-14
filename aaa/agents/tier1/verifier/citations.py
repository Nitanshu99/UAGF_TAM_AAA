"""The law behind the articles an artefact cites — F14's remaining half.

Fix 1 stopped the Verifier *denying* an article it could not see: the shared
preamble now declares itself a partial index, and the citation rule forbids a
"does not exist" finding unless retrieval positively contradicts the citation.
That closed the false finding at call #036 — *"Art. 72 … does not exist in
Regulation (EU) 2024/1689"* — but only by downgrading it to `minor`/unverified.
The Verifier still could not *verify* a citation, because it had no retrieval
channel: the five phase agents were given a ``regulatory_rag``, and the agent
whose job is checking their legal claims was not.

Its own prompt already assumed one. ``## REGULATORY CITATION VERIFICATION``
step 1 reads *"Resolve the article against Regulatory RAG output"* — an
instruction pointing at a channel that did not exist, which is F1's shape one
layer up. This module supplies the channel rather than softening the rule.

Retrieval is driven by the artefact, not by a fixed seed query: whatever
articles the artefact cites are the articles whose text the Verifier needs in
front of it. Passages, not a synthesised summary — the same reasoning that
removed :meth:`RegulatoryRAG.process`'s generation step. A paraphrase cannot
settle whether Art. 72 exists; the Article 72 text can.

**Fix 16 — and it has to be *that* article's text.** The channel above worked
and retrieved the wrong law: it asked ``rag.search(f"{ref} EU AI Act")``, and
the post-fix run's fifteen distinct citation queries returned their own
reference **once**. A named article is fetched by identifier, not by
similarity, so :meth:`RegulatoryRAG.lookup` runs first and subject-matter
search only when the corpus holds nothing under that ref — with its hits
labelled ``semantic_fallback``, because a passage that merely embeds near
"Article 72" is evidence about the neighbourhood and not about the citation.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.verifier.fetch import _fetch
from aaa.tools.evidence_retrieval.dedup import merge_hits
from aaa.tools.evidence_retrieval.logger import _no_rag
from aaa.tools.evidence_retrieval.refs import cited_references as _cited_references

logger = logging.getLogger(__name__)

#: One critique must not become a retrieval storm. An artefact citing thirty
#: articles is citing them in passing; the ones that carry its argument appear
#: first, which is why order of appearance is kept rather than sorted.
MAX_CITATIONS = 6

#: Passages per cited reference. The Verifier needs enough to confirm the
#: article exists and says what the artefact claims — not a research dossier.
TOP_K = 2


def cited_references(content: Any) -> list[str]:
    """Return the regulatory references an artefact cites, first appearance first.

    The parse itself lives in :mod:`aaa.tools.evidence_retrieval.refs`, shared
    with fix 17's seed, which asks the same question of an anchor query. What
    is local to the Verifier is the cap: :data:`MAX_CITATIONS` is a budget for
    one critique, not a property of the text.

    :param content: The artefact payload (dict or already-rendered string).
    :type content: Any
    :returns: Canonical references such as ``["Article 10", "Annex III"]``,
        capped at :data:`MAX_CITATIONS`.
    :rtype: list[str]
    """
    return _cited_references(content, limit=MAX_CITATIONS)


def retrieve_cited_law(rag: Any, content: Any, *, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """Retrieve the corpus text for every reference *content* cites.

    Never raises: a critique must still happen when retrieval is unavailable —
    it simply happens without the law, which the prompt's rule already handles
    by recording the citation unverified rather than denying it.

    :param rag: A ``RegulatoryRAG``, or ``None`` when none is wired.
    :type rag: Any
    :param content: The artefact payload under critique.
    :type content: Any
    :param top_k: Passages to pull per reference.
    :type top_k: int
    :returns: De-duplicated, score-ranked hits (fix 9's ``merge_hits``).
    :rtype: list[dict[str, Any]]
    """
    refs = cited_references(content)
    if not refs:
        return []
    if rag is None:
        _no_rag(f"Verifier citation check for {', '.join(refs)}")
        return []
    hits: list[Any] = []
    resolved: list[str] = []
    for ref in refs:
        found = _fetch(rag, ref, top_k)
        if found:
            resolved.append(ref)
        hits, _, _ = merge_hits(hits, found)
    logger.info("Verifier: %d passage(s) for %d cited reference(s); resolved by "
                "identifier: %s; unresolved: %s.",
                len(hits), len(refs), ", ".join(resolved) or "none",
                ", ".join(r for r in refs if r not in resolved) or "none")
    return hits




__all__ = ["MAX_CITATIONS", "TOP_K", "cited_references", "retrieve_cited_law"]
