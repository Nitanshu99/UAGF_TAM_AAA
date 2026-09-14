"""What actually binds *this* engagement — fix 40 (finding R8).

RetailIQ is a `limited`-tier client. Its scope is three articles:
``{Art.13, Art.50, Annex_IV}``. The audit delivered a conformity table of
**thirteen**, eleven of which do not bind it — Art. 5, 6, 9, 10, 11, 12, 14, 17,
43, 72 and Annex III — with Art. 11 reported **PASS** and the other ten
``INSUFFICIENT_EVIDENCE``. A limited-risk client was told, article by article,
that it had failed to evidence obligations it does not carry.

**The root cause is not the gate that recorded them.** ``_TEMPLATE_ARTICLES`` and
the phase runners' ``tid_articles`` are constants written when every engagement
was high-risk: the GovernanceAgent's contract claims Art. 9, 14 and 17 whatever
the tier, so fix 26's gate faithfully recorded articles its *input* should never
have contained. The repair belongs here, where scope is resolved — not as a
second gate on the gate.

The Verifier found this unaided and graded it ``material`` (case 02 #023):

    "the matrix assesses 7 articles that explicitly apply only to HIGH-RISK AI
     systems per regulatory hits … but declaration_summary confirms
     risk_tier='limited'. This is a fundamental regulatory misfire."

**Out of scope means absent, not ``NOT_APPLICABLE``.** Two reasons, and the first
is an acceptance criterion. KPI 2's denominator *is* the in-scope set, so any row
outside it makes the headline number and the table it explains describe different
audits. And ``NOT_APPLICABLE`` already carries a different meaning here — fix 27
gives it to an **in-scope** article with no per-group outcome for this task type —
so reusing it would make two distinct facts indistinguishable to a reader.

Absent is not silent, though: :func:`keep_in_scope` records what it dropped in
``out_of_scope_claims``, naming the article, the claimant and the tier that
excluded it. No finding is raised, because nothing is wrong with the *client* —
the record is a fact about the audit's own bookkeeping, and it is what lets a
reader confirm the omission was decided rather than missed.

**Scope is the tier's set plus the gate's.** Art. 25 and Art. 27 appear in no
``ARTICLE_SET``; they reach an engagement only through a Stage A flag. Reading
``_resolve_article_set`` alone would drop precisely the articles fix 24 exists to
raise — case 03's Art. 27 and case 04's Art. 50 among them.

**An unstated tier does not mean a narrow one, and the filter does not run.**
``_resolve_article_set`` falls back to ``minimal``, which is a set of *one*
article — a sensible default for a coverage denominator and a catastrophic one
for a filter, since it would erase a whole conformity table on a state whose tier
had simply not been resolved yet. Phase 1 is what establishes the tier, and R1
showed Phase 1 being lost in four of five cases. So :func:`keep_in_scope` filters
only when a tier was actually *stated*, and passes everything through otherwise —
the same reading :mod:`aaa.platform.phase_budget` gives an absent deadline.
Every real engagement carries ``declared_risk_tier`` from Stage A intake, so this
narrows nothing that matters and refuses to guess where it would.

**One obligation, two spellings.** ``ARTICLE_SET["high_llm"]`` and
``GATE_ARTICLES["is_gpai_systemic"]`` name the GPAI obligations ``GPAI_51`` …
``GPAI_55``; the L-branch's contract, and the Verifier's own ``article_citations``
in case 04, name the same five ``Art.51`` … ``Art.55``. The scope test resolves
the alias — otherwise this fix would have deleted five **admitted, PASS**
articles from a high-risk engagement, which is the opposite of what it is for.
It resolves the alias and stops there: the delivered id is left exactly as
written, because rewriting it would move case 04's coverage from 50.0 % to 75 %
inside a fix whose acceptance criterion is that the high-risk cases do not move.
That the two spellings still divide the matrix from KPI 2's denominator is
finding **R17**, and it is fix 49's.
"""
from __future__ import annotations

import logging
from typing import Any, Final, FrozenSet, Iterable

from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET, _resolve_article_set
from aaa.tools.regulatory_coverage.gate_articles import scope_gate_articles

logger = logging.getLogger(__name__)


#: One obligation, two spellings — see the module docstring. The scope test
#: resolves the alias; nothing else does, deliberately (finding R17, fix 49).
_GPAI_ALIASES: Final[dict[str, str]] = {
    f"Art.{n}": f"GPAI_{n}" for n in range(51, 56)
}


def canonical_article(article: str) -> str:
    """Return the id the article set spells this obligation with.

    :param article: An article reference as written by a template contract or by
        the Verifier's own citation.
    :returns: The canonical id, for a scope test only. Callers that *render* an
        article must keep the id they were given.
    """
    return _GPAI_ALIASES.get(article.strip(), article)


def core_article(article: str) -> str:
    """Reduce an article reference to its base form (``Art.15§1`` → ``Art.15``).

    Scope binds at the article, not the sub-article: ``Art.15§1`` is in scope
    exactly when ``Art.15`` is, and testing the raw string against a set that
    holds only base ids would drop every sub-article the high-risk cases assess.
    """
    base = article.split("§", 1)[0]
    base = base.split(" point", 1)[0]
    return base.strip()


def scope_is_known(state: Any) -> bool:
    """Whether this engagement has actually stated a risk tier.

    :param state: The AuditState dict.
    :returns: ``True`` when ``risk_tier`` or ``declared_risk_tier`` is set to a
        tier :data:`~aaa.tools.regulatory_coverage.article_set.ARTICLE_SET`
        recognises.
    """
    tier = state.get("risk_tier") or state.get("declared_risk_tier")
    return bool(tier) and tier in ARTICLE_SET


def engagement_articles(state: Any) -> FrozenSet[str]:
    """Every article that binds this engagement: the tier's set, plus the gate's.

    :param state: The AuditState dict.
    :returns: Base article ids. Sub-articles are not listed; test them with
        :func:`core_article`, which :func:`is_in_scope` does.
    """
    return frozenset(_resolve_article_set(state)) | frozenset(scope_gate_articles(state))


def is_in_scope(state: Any, article: str) -> bool:
    """Whether *article* — or the article it is a sub-article of — binds *state*."""
    scope = engagement_articles(state)
    canonical = canonical_article(article)
    return (canonical in scope
            or canonical_article(core_article(article)) in scope)


def keep_in_scope(state: dict, articles: Iterable[str], *, claimed_by: str = "") -> list[str]:
    """Return only the articles that bind this engagement, recording the rest.

    :param state: The mutable AuditState dict; ``out_of_scope_claims`` is
        appended to when anything is dropped.
    :param articles: The articles a phase, template or gate is claiming.
    :param claimed_by: What claimed them — a template id, a phase label — so the
        record can be read back to the contract that needs correcting.
    :returns: The kept articles, in the order given.
    """
    articles = list(articles)
    if not scope_is_known(state):
        return articles
    kept: list[str] = []
    dropped: list[str] = []
    for article in articles:
        (kept if is_in_scope(state, article) else dropped).append(article)
    if dropped:
        tier = state.get("risk_tier", state.get("declared_risk_tier", "minimal"))
        state.setdefault("out_of_scope_claims", []).extend(
            {"article": a, "claimed_by": claimed_by, "risk_tier": tier}
            for a in dropped
            if not any(c.get("article") == a and c.get("claimed_by") == claimed_by
                       for c in state.get("out_of_scope_claims") or []))
        logger.info(
            "%s claimed %d article(s) outside a '%s' engagement's scope; not "
            "recorded against the client: %s",
            claimed_by or "a phase", len(dropped), tier, ", ".join(dropped))
    return kept


__all__ = ["canonical_article", "core_article", "engagement_articles",
           "is_in_scope", "keep_in_scope", "scope_is_known"]
