"""Part 2 of the former ``compliance_matrix`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.logger import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _CORE_HIGH_RISK_ARTICLES,
    _TEMPLATE_ARTICLES,
    _core_article,
    logger,
)
from aaa.platform.state.admission import admitted_artefacts
from aaa.tools.regulatory_coverage.artefact_contract import contract_for
from aaa.tools.regulatory_coverage.engagement_scope import canonical_article, core_article


def _cited_within_contract(state: dict, tid: str) -> set[str]:
    """The articles *tid*'s critique cites that *tid* is accountable for — fix 50.

    A citation is the Verifier's, and the Verifier reads one artefact against one
    contract. A citation outside that contract is the model attributing evidence
    to an article nobody asked this artefact about, which is the class of defect
    findings **R15** and **R17** both turned out to be — and it is how a critique
    written before fix 47 still admits ``Art.15§1`` from an output sampling log
    whose contract is ``Art.10§2(f)``.

    Both ends are compared canonically, so the spelling reconciliation fix 49
    made at this boundary still holds: an artefact cited as ``Art.53`` evidences
    ``GPAI_53`` when its contract names it.

    An artefact with **no** contract entry admits nothing from its citations and
    says so at ``WARNING``: that is a gap in
    :data:`~aaa.tools.regulatory_coverage.artefact_contract.ARTEFACT_ARTICLES`,
    which fix 41's ownership guard is what catches, and silently trusting an
    unconstrained citation is the behaviour this fix removes.
    """
    cited = ((state.get("verifier_critiques", {}) or {}).get(tid) or {}).get(
        "article_citations") or []
    if not cited:
        return set()
    contract = contract_for(tid)
    if contract is None:
        logger.warning(
            "%s has no entry in ARTEFACT_ARTICLES, so its %d citation(s) admit "
            "nothing: %s. An artefact with no contract cannot be checked against "
            "one.", tid, len(cited), ", ".join(str(a) for a in cited))
        return set()
    allowed = {canonical_article(core_article(a)): canonical_article(a)
               for a in contract}
    kept, over = set(), []
    for article in cited:
        key = canonical_article(core_article(str(article)))
        if key in allowed:
            kept.add(canonical_article(str(article)))
        else:
            over.append(str(article))
    if over:
        logger.info(
            "%s cited %s, which %s is not accountable for (%s). The citation does "
            "not admit them.", tid, ", ".join(over), tid, ", ".join(contract))
        state.setdefault("over_cited_articles", []).extend(
            {"template_id": tid, "article": a, "contract": list(contract)}
            for a in over
            if not any(c.get("template_id") == tid and c.get("article") == a
                       for c in state.get("over_cited_articles") or []))
    return kept


def _collect_admitted_articles(state: dict) -> set[str]:
    """Collect every article admitted by a verifier-accepted artefact.

    The four scope-gate flags used to be admitted here too.  They say an
    obligation *applies*, not that it is met, so they now feed
    :func:`~aaa.agents.tier1.phases.compliance_matrix.scope_articles.scope_gate_articles`
    instead — scope, not evidence.
    """
    admitted: set[str] = set()

    # The intake artefacts' articles used to be added from a second rule reading
    # ``phase_artefacts`` directly; ``admitted_artefacts`` folds that in, so the
    # question "may this artefact support a verdict?" now has one answer.
    for tid in admitted_artefacts(state):
        # Fix 50: a citation admits an article only if the artefact was
        # accountable for it. Fix 49 normalises the spelling; this bounds the set.
        admitted.update(_cited_within_contract(state, tid))
        admitted.update(_TEMPLATE_ARTICLES.get(tid, []))

    return admitted
