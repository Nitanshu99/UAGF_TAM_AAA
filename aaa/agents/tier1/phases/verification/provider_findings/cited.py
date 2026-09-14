"""Which of a template's articles one Verifier provider issue is about.

Every provider issue used to be recorded on all of its template's articles. On case
06 (MiniMax run, 2026-09-14) a T14 issue about the provider's governing artefacts
"required by Articles 9, 10, 13, 15, and 17" therefore failed Art. 14 as well, and a
T15 issue about Art. 72 and Art. 73 failed Art. 12 — articles the issue never named.
"""
from __future__ import annotations

import re
from typing import Any

#: "Art. 10(2)(f)", "Article 13", "Arts. 9, 10 and 17", "Articles 72(1) and 73".
_REFERENCE = re.compile(
    r"\bArt(?:icle)?s?\.?\s*(\d+(?:\s*\(\d+\))?(?:\s*\([a-z]\))?"
    r"(?:(?:\s*,\s*(?:and\s+|or\s+)?|\s+(?:and|or|&)\s+)\d+(?:\s*\(\d+\))?(?:\s*\([a-z]\))?)*)",
    re.IGNORECASE)
_ONE = re.compile(r"(\d+)\s*(?:\((\d+)\))?\s*(?:\(([a-z])\))?", re.IGNORECASE)


def _references(text: str) -> list[tuple[str, str | None, str | None]]:
    """``(article, paragraph, point)`` for each article reference in *text*."""
    return [(m.group(1), m.group(2), m.group(3)) for ref in _REFERENCE.finditer(text)
            for m in _ONE.finditer(ref.group(1))]


def _canonical(ref: tuple[str, str | None, str | None], articles: list[str]) -> str | None:
    """The most specific of the template's ids the reference names, if any."""
    number, paragraph, point = ref
    for candidate in (f"Art.{number}§{paragraph}({point})" if paragraph and point else None,
                      f"Art.{number}§{paragraph}" if paragraph else None, f"Art.{number}"):
        if candidate in articles:
            return candidate
    return None


def referenced_articles(text: str) -> list[str]:
    """``Art.N`` for each article *text* refers to, in order, without repeats.

    :param text: Free text such as a Verifier issue's description.
    """
    return list(dict.fromkeys(f"Art.{number}" for number, _, _ in _references(text)))


def cited_articles(issue: dict[str, Any], articles: list[str]) -> list[str]:
    """The template articles *issue* is about; all of them when it names none.

    :param issue: A Verifier issue; an explicit ``articles`` list wins over its text.
    :param articles: The template's articles, in scope.
    """
    explicit = [a for a in issue.get("articles") or [] if a in articles]
    if explicit:
        return explicit
    text = " ".join(str(issue.get(k) or "") for k in ("field", "description"))
    named = [a for ref in _references(text) if (a := _canonical(ref, articles))]
    return list(dict.fromkeys(named)) or list(articles)


__all__ = ["cited_articles", "referenced_articles"]
