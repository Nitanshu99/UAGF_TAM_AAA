"""Articles the Stage A scope gate brings into scope.

Split out of :mod:`aaa.agents.tier1.phases.compliance_matrix.scope_articles` by
fix 40, which needs the *question* — what does this engagement's scope contain? —
answered below the agent layer, where KPI 2's article set already lives. The
finding half (``record_scoped_unevidenced``) stays where it was; only the pure
lookup moves, and the old module re-exports it, so every existing import is
unchanged.

A gate flag brings an article into scope that the tier alone would not: Art. 25
and Art. 27 are in **no** ``ARTICLE_SET`` at all, so an engagement's real scope is
the tier's set *plus* whatever the gate added. Reading the tier alone would drop
exactly the articles fix 24 exists to raise.
"""
from __future__ import annotations

from typing import Final

#: Scope-gate flag → the articles it brings into scope.
GATE_ARTICLES: Final[dict[str, tuple[str, ...]]] = {
    "become_provider_under_art25": ("Art.25",),
    "triggers_fria": ("Art.27",),
    "triggers_art50_transparency": ("Art.50",),
    # This flag used to add the literal string ``"Arts.51-55"``, which no
    # ``ARTICLE_SET``, ``_TEMPLATE_ARTICLES`` row or ``ARTICLE_PHASE`` entry
    # recognises: the article could be asserted ``PASS`` and could never be
    # assessed, because nothing else in the system spells it that way.  The
    # canonical ids are the five KPI 2 already counts for a GPAI engagement.
    "is_gpai_systemic": ("GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55"),
}


def scope_gate_articles(state: dict) -> dict[str, str]:
    """Articles the scope gate brings into scope, mapped to the flag that did it.

    :param state: Live audit state carrying ``scope_gate``.
    :returns: ``{article: flag}`` for every flag the gate set.
    """
    gate = state.get("scope_gate", {}) or {}
    return {article: flag
            for flag, articles in GATE_ARTICLES.items() if gate.get(flag)
            for article in articles}


__all__ = ["GATE_ARTICLES", "scope_gate_articles"]
