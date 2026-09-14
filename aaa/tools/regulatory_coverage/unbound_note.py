"""The sentence that says which mapped articles are not among the engagement's binding articles.

Phase 5 writes it into T14 (:mod:`aaa.agents.tier2.governance_agent.scope_note`) and the
verification gate reads it back, so the two share one spelling. The rehearsal of case 06
from a fresh clone (2026-09-14) had the Verifier assert that the sentence was wrong — that
the articles it names *are* among ``binding_articles`` — while the list it held contained
none of them (T-20260915-001). A membership statement is checkable, so it is
checked rather than left to the Verifier's materiality label.
"""
from __future__ import annotations

import re

#: What the sentence asserts about the articles it names.
NOT_AMONG = "none of these is among this engagement's binding_articles"

_STATED = re.compile(r"maps controls to (?P<articles>[^;]+); " + re.escape(NOT_AMONG))


def unbound_sentence(articles: list[str]) -> str:
    """The clause naming *articles* as outside ``binding_articles``.

    :param articles: Article ids the assessment maps and the engagement does not bind.
    """
    return f"The self-assessment also maps controls to {', '.join(articles)}; {NOT_AMONG}"


def stated_unbound(text: str) -> list[str]:
    """The article ids a sentence written by :func:`unbound_sentence` names in *text*; ``[]`` if none.

    :param text: Any artefact text, such as T14's ``phase5_narrative_summary``.
    """
    found = _STATED.search(text or "")
    return [a.strip() for a in found.group("articles").split(",")] if found else []


__all__ = ["NOT_AMONG", "stated_unbound", "unbound_sentence"]
