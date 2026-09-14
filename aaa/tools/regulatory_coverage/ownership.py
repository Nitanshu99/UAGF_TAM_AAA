"""Which phase can actually deliver an article's evidence — fix 41 (finding R9).

RetailIQ's in-scope set is ``{Art.13, Art.50, Annex_IV}``. **Art. 50 — the only
substantive transparency obligation a limited-risk system carries — was assessed
by nothing**, and the delivered matrix did not even list it. Fix 31 added a guard
asserting that every article in ``ARTICLE_SET["high"]`` has an accountable
template; that guard could not see this, because it checked one tier and asked
one question.

Two questions have to be asked, per tier:

*Does anything own it?*  An article no template evidences cannot be assessed by
any schedule. Fix 47 turned this from a theoretical case into a real one: Art. 50
*looked* owned because ``_TEMPLATE_ARTICLES`` attributed it to the two fairness
artefacts, which examine outputs for bias and say nothing about disclosure.
Removing the mis-attribution revealed the hole rather than creating it.

*Is its owner scheduled?*  An owner the CSP planner marks ``O`` or ``S`` for this
tier is an owner that will not run. This is the half fix 31 had no way to reach,
and it is why an article can pass an ownership check and still go unassessed.

**An article has more than one owner, and that matters.** ``ARTICLE_PHASE`` maps
an article to *one* phase because T17 prints one ``source_phase``; using it to
answer schedulability gives the wrong answer for a high-risk **LLM** engagement,
where the planner skips P3 outright (``p3 == "S"``) and Art. 15's evidence arrives
through the cybersecurity spawn's T11 extension and the L-branch instead. So the
owner set is derived from the template map, and an article is schedulable when
**any** phase that emits an owning template is mandatory.

**Which repair, and why.** The backlog offers two: make the planner mark an
owning phase mandatory when its articles are in scope, or fail the build and have
a human resolve it per tier. This module implements the **second**, because the
first cannot work for the gaps that actually exist. Three of the four are missing
*artefacts*, not missing schedules — no phase the planner could schedule produces
evidence of Art. 50 disclosure — and forcing such a phase to run would manufacture
the appearance of coverage without adding a line of evidence, which is the class
of defect thirty-odd fixes have been removing. Where a gap is genuinely a
schedule, the owner set already resolves it without touching the planner.

:data:`KNOWN_UNOWNED` is how the remaining gaps stay honest: each is declared with
its reason and the fix that closes it, the guard asserts the set is **exactly**
that, and a new hole therefore fails the build.
"""
from __future__ import annotations

from typing import Final

from aaa.tools.regulatory_coverage.engagement_scope import canonical_article, core_article
from aaa.tools.regulatory_coverage.unowned import KNOWN_UNOWNED

#: Which phase emits which template. A template listed against several phases is
#: produced by one and *extended* by the others — T11 by P3 then the cyber spawn,
#: T08 by P2 then the privacy spawn — and either can carry its article's evidence.
TEMPLATE_PHASE: Final[dict[str, tuple[str, ...]]] = {
    "T01a_stage_a_triage": ("INTAKE",),
    "T01b_annex_iv_dossier": ("INTAKE",),
    "T01c_intake_completeness_report": ("INTAKE",),
    "T02_system_card": ("P1",), "T03_annex_iii_mapping": ("P1",),
    "T04_risk_tier_decision": ("P1",), "T05_art43_decision": ("P1",),
    "T06_datasheet_for_datasets": ("P2",), "T07_data_quality_report": ("P2",),
    "T08_special_category_data_log": ("P2", "PRIV"),
    "T09_model_card": ("P3",), "T10_explainability_report": ("P3",),
    "T11_robustness_report": ("P3", "CYBER"),
    "T12_output_fairness_report": ("P4",), "T13_output_sampling_log": ("P4",),
    "T14_governance_findings": ("P5",), "T15_monitoring_logging_review": ("P5",),
    "T16_uagf_tam_l_evidence": ("L",),
    "T17_compliance_matrix": ("P6",), "T18_audit_report": ("P6",),
}

#: Phases that are not the planner's to schedule: intake runs before it, and P6
#: is reached by FINALIZE rather than by a plan entry.
ALWAYS_RUN: Final[frozenset[str]] = frozenset({"INTAKE", "P6"})




def article_owners(article: str, template_articles: dict[str, list[str]]) -> set[str]:
    """The phases that emit a template evidencing *article*.

    :param article: An article id, sub-article or GPAI alias.
    :param template_articles: The template → articles map to read ownership from.
    :returns: Phase keys; empty when nothing owns it.
    """
    wanted = {article, core_article(article), canonical_article(article),
              canonical_article(core_article(article))}
    return {phase
            for tid, articles in template_articles.items()
            if wanted & {a for art in articles
                         for a in (art, core_article(art), canonical_article(art))}
            for phase in TEMPLATE_PHASE.get(tid, ())}


def is_schedulable(article: str, plan: dict[str, str],
                   template_articles: dict[str, list[str]]) -> bool:
    """Whether some phase that can evidence *article* is mandatory in *plan*.

    "Any", not "all": T11 is emitted by P3 and extended by the cyber spawn, so an
    engagement whose planner skips P3 can still evidence Art. 15 through CYBER.
    Asking ``ARTICLE_PHASE`` — one article, one phase — gets that wrong.

    :param article: An article id.
    :param plan: The CSP phase plan, ``{phase: "M" | "O" | "S"}``.
    :param template_articles: The template → articles map.
    :returns: ``True`` when at least one owning phase is mandatory or always runs.
    """
    owners = article_owners(article, template_articles)
    return any(p in ALWAYS_RUN or plan.get(p) == "M" for p in owners)


__all__ = ["ALWAYS_RUN", "KNOWN_UNOWNED", "TEMPLATE_PHASE", "article_owners",
           "is_schedulable"]
