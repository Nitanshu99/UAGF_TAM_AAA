"""Fetch a named regulatory unit by identifier — finding P1.

**A citation is not a search query.** The Verifier's citation channel (fix 14)
asked the corpus ``f"{ref} EU AI Act"`` — a bare label with almost no
discriminating content, since every chunk in the corpus is *about* the EU AI
Act. Of the fifteen distinct citation queries the post-fix run made, **one**
returned its own reference: ``Article 10 EU AI Act`` came back with Recital 94
and Recital 39, ``Article 72 EU AI Act`` with Articles 74 and 71. The channel
ran on twenty of twenty-one critiques and handed the Verifier the wrong law
almost every time.

Re-ranking cannot rescue that, and neither can a better embedding: retrieving
*the article named X* is a lookup by identifier, and vector similarity is the
wrong instrument for an identifier. The corpus already stores ``ref`` as an
indexed keyword payload field (``FILTER_KEYS`` in the ingestion config), so the
question has an exact answer available — ``ref == "Article 72"`` — and this
module asks it that way.

Two consequences worth stating. There is nothing for a cross-encoder to judge
here, so the lookup path skips re-ranking entirely, which is also P2's
vague-query saturation removed at the source rather than thresholded around.
And no query is embedded, so the corpus-provider guard has nothing to check and
is not invoked — an exact-match read is valid whatever embedded the corpus.
"""
from __future__ import annotations

from aaa.agents.tier1.regulatory_rag.lookup.annotate import DEFAULT_REGULATION, annotate
from aaa.agents.tier1.regulatory_rag.lookup.kb import _kb_ref, kb_lookup
from aaa.agents.tier1.regulatory_rag.lookup.qdrant import qdrant_lookup

__all__ = ["DEFAULT_REGULATION", "_kb_ref", "annotate", "kb_lookup", "qdrant_lookup"]
