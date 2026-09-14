"""Which admitted artefacts evidence an article, and the verdict ladder applied to it."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.logger import _TEMPLATE_ARTICLES, _core_article
from aaa.platform.state.admission import admitted_artefacts, artefact_verdict
from aaa.tools.regulatory_coverage.artefact_contract import contract_for
from aaa.tools.regulatory_coverage.engagement_scope import canonical_article, core_article


def _contracted_for(tid: str, article: str) -> bool:
    """Whether *tid* is accountable for *article* — fix 50.

    Compared on the canonical base id at both ends, so ``Art.15§1`` is covered by
    a contract naming ``Art.15`` and ``Art.53`` by one naming ``GPAI_53``.
    """
    contract = contract_for(tid)
    if contract is None:
        return False
    wanted = canonical_article(core_article(article))
    return wanted in {canonical_article(core_article(a)) for a in contract}


def _candidate_tids(state: dict, article: str) -> list[str]:
    """Template ids that name *article*, whatever the Verifier made of them.

    Citations first, then the template map — the order the evidence list has
    always been printed in.  Admission is not consulted here: the partition into
    cited and excluded is the caller's, and both halves need the same candidates.
    """
    # Fix 49 (R17): matched on the canonical id at both ends, so an artefact
    # cited as `Art.51` still evidences `GPAI_51` and the row keeps its basis.
    # Fix 50: and only when the artefact is accountable for it. A citation that
    # exceeds its contract does not admit an article (`_collect_admitted_articles`),
    # so it must not be *listed* as that article's evidence either — a row saying
    # "evidenced by T13" beside a verdict of INSUFFICIENT_EVIDENCE is the same
    # contradiction one field over.
    wanted = canonical_article(article)
    tids = [tid for tid, crit in (state.get("verifier_critiques", {}) or {}).items()
            if wanted in {canonical_article(a)
                          for a in ((crit or {}).get("article_citations") or [])}
            and _contracted_for(tid, article)]
    artefacts = state.get("phase_artefacts", {}) or {}
    for tid, arts in _TEMPLATE_ARTICLES.items():
        if wanted in {canonical_article(a) for a in arts} and tid in artefacts \
                and tid not in tids:
            tids.append(tid)
    return tids


def _supporting_tids(state: dict, article: str) -> list[str]:
    """Admitted template ids that evidence an article (via citations + template map)."""
    admitted = admitted_artefacts(state)
    return [tid for tid in _candidate_tids(state, article) if tid in admitted]


def _excluded_tids(state: dict, article: str) -> list[tuple[str, str]]:
    """``(template id, verdict)`` for artefacts naming *article* that were not admitted."""
    admitted = admitted_artefacts(state)
    return [(tid, artefact_verdict(state, tid))
            for tid in _candidate_tids(state, article) if tid not in admitted]


def _article_verdict(article: str, art_findings: list[dict], admitted: set[str],
                     insufficient: set[str]) -> str:
    """Apply the verdict precedence ladder to one article.

    :param article: The article reference under assessment.
    :param art_findings: Findings mapped to this article.
    :param admitted: Articles with admitted, verifier-accepted evidence.
    :param insufficient: Articles whose independent analysis was not performed.
    """
    has_material = any(f.get("materiality") == "material" for f in art_findings)
    has_qual = any(
        f.get("materiality") in {"possibly_material", "observation"} for f in art_findings)
    if has_material:
        return "FAIL"
    if article in insufficient or _core_article(article) in insufficient:
        return "INSUFFICIENT_EVIDENCE"
    if has_qual:
        return "PASS_WITH_OBSERVATIONS"
    if article in admitted:
        return "PASS"
    return "INSUFFICIENT_EVIDENCE"


__all__ = ["_article_verdict", "_candidate_tids", "_excluded_tids", "_supporting_tids"]
