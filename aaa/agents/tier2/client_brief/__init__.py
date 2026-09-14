"""client_brief — the audit result rewritten for the customer, article by article."""
from aaa.agents.tier2.client_brief.agent import ClientBriefAgent  # noqa: F401
from aaa.agents.tier2.client_brief.bundle import article_bundle, audited_articles  # noqa: F401
from aaa.agents.tier2.client_brief.constants import TEMPLATE_ID  # noqa: F401
from aaa.agents.tier2.client_brief.markdown import render_brief  # noqa: F401

__all__ = [
    "ClientBriefAgent",
    "TEMPLATE_ID",
    "article_bundle",
    "audited_articles",
    "render_brief",
]
