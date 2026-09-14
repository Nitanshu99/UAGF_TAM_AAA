"""The articles a risk tier brings into scope — fix 51 (finding R18).

**Art. 50 is not here, and that is the fix.** It used to appear in all five tier
sets, so a tabular credit scorer sold B2B to a bank — used by a licensed credit
officer, interacting with no natural person — was assessed against the obligation
to tell natural persons they are talking to an AI. Four of the five cases in the
2026-09-03 run carried it that way, and Stage A had said in every one of them that
it does not apply.

Art. 50 is **conditional**: the Act's transparency chapter binds systems that
interact directly with natural persons, generate synthetic content, or perform
emotion recognition or biometric categorisation. This system already models that
correctly — ``GATE_ARTICLES["triggers_art50_transparency"]`` — and Stage A set the
flag ``True`` for exactly one case, the LLM/agentic one. Declaring it here *as
well* meant the obligation was scoped twice and the unconditional half was wrong.

The consequence had been masked for three fixes: Art. 50 looked evidenced because
``_TEMPLATE_ARTICLES`` attributed it to the two fairness artefacts (fix 47), then
looked merely unowned (fix 41), then became visibly unevidenceable in every tier
(fix 50) — at which point a ``minimal`` engagement, whose whole scope was
``{Art.50}``, scored 0.0 % coverage and always disclaimed. The article was never
the audit's to evidence unconditionally; it was the gate's to raise.

``minimal`` is now empty, and that is the correct reading rather than a hole: a
minimal-risk system carries no mandatory requirements under the Act. See
:func:`~aaa.tools.regulatory_coverage.covered_articles.covered_articles` for how
an empty scope is reported, which is deliberately not "100 % covered".
"""
from __future__ import annotations

from typing import TYPE_CHECKING, FrozenSet

from aaa.platform.state.stage_a_lookup import stage_a_field

if TYPE_CHECKING:
    from aaa.platform.state import AuditState

ARTICLE_SET: dict[str, FrozenSet[str]] = {
    "high": frozenset({
        "Art.5", "Art.6", "Art.9", "Art.10", "Art.11", "Art.12", "Art.13",
        "Art.14", "Art.15", "Art.17", "Art.43", "Art.72",
        "Annex_III", "Annex_IV",
    }),
    "high_llm": frozenset({
        "Art.5", "Art.6", "Art.9", "Art.10", "Art.11", "Art.12", "Art.13",
        "Art.14", "Art.15", "Art.17", "Art.43", "Art.72",
        "Annex_III", "Annex_IV", "GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54",
        "GPAI_55",
    }),
    "limited": frozenset({
        "Art.13", "Annex_IV",
    }),
    # A minimal-risk system carries no mandatory requirements under the Act; the
    # transparency obligation it used to hold here is conditional and belongs to
    # the Stage A gate (fix 51, R18).
    "minimal": frozenset(),
    "gpai": frozenset({
        "Art.5", "Art.6", "Art.11", "Art.12", "Art.72", "Annex_IV",
        "GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55",
        "Annex_XI", "Annex_XII",
    }),
    "prohibited": frozenset(),
}


_ADMITTED_VERDICTS = {"accept", "accept_with_notes"}


#: Articles 51-55 bind *providers of* a general-purpose AI model. A system that
#: consumes a third-party GPAI model as a component carries value-chain duties,
#: not these.
GPAI_PROVIDER_OBLIGATIONS: FrozenSet[str] = frozenset({
    "GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55",
})


def _places_gpai_on_market(state: AuditState) -> bool:
    """Whether the provider declared it places a GPAI model on the market.

    Absent means unknown, and the conservative reading keeps the obligations in
    scope. Only an explicit ``False`` removes them.

    :param state: Audit state or declaration summary carrying Stage A.
    :returns: True unless the declaration explicitly says otherwise.
    :rtype: bool
    """
    declared = stage_a_field(state, "gpai_general_purpose")
    return True if declared is None else bool(declared)


def _resolve_article_set(state: AuditState) -> FrozenSet[str]:
    """Choose the correct in-scope article set given state.

    The generative modality alone used to pull in Arts. 51-55, so a system that
    merely *consumes* a hosted GPAI model was assessed — and could be passed —
    against obligations that do not bind it. On the Mariposa engagement that
    put five unbindable articles in the denominator and passed all five,
    inflating regulatory coverage from 42.9 % to 60.0 %.
    """
    tier = state.get("risk_tier", state.get("declared_risk_tier", "minimal"))
    is_llm = state.get("is_llm_or_agentic", False)

    if tier == "high" and is_llm:
        articles = ARTICLE_SET["high_llm"]
        if not _places_gpai_on_market(state):
            return articles - GPAI_PROVIDER_OBLIGATIONS
        return articles
    return ARTICLE_SET.get(tier, frozenset())
