"""Choosing which answering units of a passage become the quote."""
from __future__ import annotations

import re
from typing import Any, Iterable

from aaa.tools.document_evidence.ground import (
    ENDS,
    Evidence,
    Question,
    about_subject,
    answers,
    units,
)

_MAX_QUOTE = 320
#: ``store_file`` names an upload ``<role>_<sha256[:8]>_<filename>``.
_STORED_PREFIX = re.compile(r"^[a-z0-9_]+_[0-9a-f]{8}_")


def _distinct(found: list[str], limit: int) -> list[str]:
    """The shortest whole sentences, then fragments, not repeating one another, in order."""
    chosen: list[str] = []
    for unit in sorted(found, key=lambda u: (not u.endswith(ENDS), len(u))):
        if len(chosen) < limit and not any(unit in c or c in unit for c in chosen):
            chosen.append(unit)
    return sorted(chosen, key=found.index)


def document_name(uri: str) -> str:
    """The uploaded file's own name, without the store's role and hash prefix."""
    name = uri.rsplit("/", 1)[-1] or uri
    return _STORED_PREFIX.sub("", name) or name


def ground(passages: Iterable[dict[str, Any]], question: Question) -> Evidence | None:
    """The answering units of the best-scored passage that has any, or ``None``.

    :param passages: ``{text, source_uri, score}`` hits, declared fields included.
    :param question: What must be said.
    """
    for passage in sorted(passages, key=lambda p: -float(p.get("score") or 0.0)):
        uri = str(passage.get("source_uri") or "")
        about = about_subject(uri, question)
        found = [u for u in units(str(passage.get("text") or "")) if answers(u, question, about)]
        if found:
            quote = " | ".join(u[:_MAX_QUOTE] for u in _distinct(found, question.limit))
            return Evidence(quote, uri, document_name(uri))
    return None


__all__ = ["document_name", "ground"]
