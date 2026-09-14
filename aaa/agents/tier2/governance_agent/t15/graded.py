"""T15's three article blocks, graded where they bind and marked not applicable where not."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.t15.applicability import (
    BLOCKS,
    not_applicable,
    unbound_blocks,
)
from aaa.agents.tier2.governance_agent.t15.articles import article_sections
from aaa.agents.tier2.governance_agent.t15.evidence import Found
from aaa.agents.tier2.governance_agent.t15.grading import grade_art12, grade_art72
from aaa.agents.tier2.governance_agent.t15.sections import overall_ops_verdict, verdict_from_qms


def graded_articles(t01b: dict[str, Any], found: Found,
                    scope: dict[str, Any] | None) -> tuple[dict[str, Any], str, list[str]]:
    """Grade Art. 12 / 17 / 72 for the engagement's scope.

    :param t01b: Annex IV dossier.
    :param found: Grounded answers to the T15 questions.
    :param scope: State-like ``{risk_tier, …}``.
    :returns: ``(article blocks, overall ops verdict, observations of binding articles)``.
    """
    monitoring = bool((t01b.get("monitoring_measures") or "").strip())
    harmonised = list(t01b.get("harmonised_standards", []) or [])
    post_market_uri = t01b.get("post_market_plan_uri")
    art12 = grade_art12((t01b.get("logging_capabilities") or "").strip(), found)
    art72 = grade_art72(bool(post_market_uri or monitoring), found)
    art17 = verdict_from_qms(harmonised, monitoring)
    articles = article_sections((art12, art17, art72), harmonised, post_market_uri, found,
                                list(t01b.get("other_standards") or []))
    unbound = unbound_blocks(scope)
    for block in unbound:
        articles[block] = not_applicable(articles[block], BLOCKS[block],
                                         str((scope or {}).get("risk_tier")))
    applicable = [b["status"] for name, b in articles.items() if name not in unbound]
    observations = (([] if "art12_record_keeping" in unbound else art12.observations)
                    + ([] if "art72_post_market_plan" in unbound else art72.observations))
    return articles, overall_ops_verdict(applicable) if applicable else "NOT_APPLICABLE", observations
