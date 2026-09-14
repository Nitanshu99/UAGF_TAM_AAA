"""Composing the brief: one model call per audited article, then one for the opening.

Per-article calls are what make the brief specific — a single pass over seventeen
requirements produces seventeen restatements of the verdict table. A breaker stops
asking once the provider has failed ``FAILURES_BEFORE_GIVING_UP`` times in a row.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.client_brief.article_pass import write_article_section
from aaa.agents.tier2.client_brief.bundle import article_bundle, audited_articles
from aaa.agents.tier2.client_brief.fallback import deterministic_section
from aaa.agents.tier2.client_brief.markdown import render_brief
from aaa.agents.tier2.client_brief.synthesis import deterministic_overview, write_overview

logger = logging.getLogger(__name__)

#: Consecutive failed section calls after which the provider is treated as down.
FAILURES_BEFORE_GIVING_UP = 3


async def build_brief(agent: Any, state: dict[str, Any], engagement_id: str) -> str:
    """Write the brief for *state* and return it as Markdown.

    One model call per audited article, then one for the opening. Per-article
    calls are what make the brief specific: a single pass over seventeen
    requirements produces seventeen restatements of the verdict table.

    :param agent: The :class:`ClientBriefAgent` making the calls.
    :param state: Final ``AuditState``, after the compliance matrix is set.
    :param engagement_id: Engagement identifier.
    :returns: The complete Markdown brief.
    """
    articles = audited_articles(state)
    logger.info("Client brief: writing %d article section(s) for %s.",
                len(articles), engagement_id)
    sections: list[dict[str, Any]] = []
    consecutive = 0
    for article in articles:
        bundle = article_bundle(article, state, agent.store)
        if consecutive >= FAILURES_BEFORE_GIVING_UP:
            sections.append(deterministic_section(bundle))
            continue
        section = await write_article_section(agent, bundle, agent.rag, engagement_id)
        consecutive = 0 if section.get("llm_written") else consecutive + 1
        if consecutive == FAILURES_BEFORE_GIVING_UP:
            logger.error(
                "Client brief: %d consecutive section(s) failed, so the "
                "provider is not answering; the remaining %d are assembled "
                "deterministically rather than attempted one at a time.",
                consecutive, len(articles) - len(sections) - 1)
        sections.append(section)
    # Asking for the opening after the breaker has tripped buys one more
    # timeout and no prose.
    overview = (deterministic_overview(state) if consecutive >= FAILURES_BEFORE_GIVING_UP
                else await write_overview(agent, state, sections))
    return render_brief(state, engagement_id, sections, overview)


__all__ = ["FAILURES_BEFORE_GIVING_UP", "build_brief"]
