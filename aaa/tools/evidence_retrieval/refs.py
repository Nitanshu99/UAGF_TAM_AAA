"""Which regulatory units a piece of text names.

Extracted from :mod:`aaa.agents.tier1.verifier.citations`, where fix 14 first
needed it, because fix 17 needs the same question asked of a *seed query*
rather than of an artefact. The Verifier asks "which articles does this
artefact cite, so I can check them"; the seed asks "which articles does this
anchor query name, so I can fetch them instead of hoping similarity surfaces
them". One regex, one canonical spelling, one place.

The parse is deliberately shallow: the paragraph pinpoint is dropped, because
the corpus is chunked per unit and ``Art. 10§2(f)`` and ``Art. 10§5`` are both
answered by the same two Article 10 chunks. Keeping the pinpoint would spend
the budget on duplicates of one article.
"""
from __future__ import annotations

import json
import re
from typing import Any

#: ``Art. 10§2(b)``, ``Art.72``, ``Article 15`` → the article number.
ARTICLE_RE = re.compile(r"\bArt(?:icle)?\.?\s*(\d{1,3})\b", re.IGNORECASE)

#: ``Annex III``, ``Annex IV`` — cited as often as articles in scope artefacts.
ANNEX_RE = re.compile(r"\bAnnex[\s_]+([IVX]{1,6})\b", re.IGNORECASE)


def cited_references(content: Any, limit: int | None = None) -> list[str]:
    """Return the regulatory references *content* names, first appearance first.

    Order of appearance is kept rather than sorted: whatever carries the
    argument is written first, both in an artefact's rationale and in a seed
    query's leading terms.

    :param content: Text, or any payload rendered to JSON before matching.
    :type content: Any
    :param limit: Maximum references to return; ``None`` for all of them.
    :type limit: int | None
    :returns: Canonical references such as ``["Article 10", "Annex III"]``.
    :rtype: list[str]
    """
    text = content if isinstance(content, str) else json.dumps(content, default=str)
    refs = [f"Article {int(n)}" for n in ARTICLE_RE.findall(text)]
    refs += [f"Annex {a.upper()}" for a in ANNEX_RE.findall(text)]
    unique = list(dict.fromkeys(refs))
    return unique[:limit] if limit is not None else unique


__all__ = ["ANNEX_RE", "ARTICLE_RE", "cited_references"]
