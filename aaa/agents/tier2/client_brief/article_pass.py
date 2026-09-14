"""One LLM pass per article: turn its evidence bundle into a readable section."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier2.client_brief.constants import PROMPT_NAME, article_title
from aaa.agents.tier2.client_brief.fallback import deterministic_section
from aaa.tools.evidence_retrieval import (
    acompletion_json_react,
    seed_client_doc_hits,
    seed_regulatory_hits,
)

logger = logging.getLogger(__name__)

#: Keys the renderer reads. Asserted at the answer position so a reply that
#: explains nothing is refused and falls back, rather than rendering as a
#: heading with empty prose underneath.
_CONTRACT: tuple[str, ...] = ("headline", "what_the_evidence_shows")

#: Prose keys the renderer will print if present, in the order it prints them.
SECTION_KEYS: tuple[str, ...] = (
    "headline", "what_you_told_us", "what_the_evidence_shows",
    "why_this_verdict", "regulatory_basis", "what_is_working", "what_to_do",
)


def _anchor_query(article: str) -> str:
    """Return the regulatory search anchor for *article*.

    Naming the article id explicitly matters: the seed resolves the references
    an anchor names by exact lookup, so the section is grounded in the article's
    own text rather than whatever embedded nearest to its subject.
    """
    return (f"{article} {article_title(article)} — obligations on the provider "
            f"of a high-risk AI system, and the GDPR provisions that overlap them")


def _doc_query(bundle: dict[str, Any]) -> str:
    """The customer-document search for this article's own subject.

    Every ClientBrief call in the 2026-09-09 run showed ``client_doc_hits[0]``:
    the brief was quoting the audit's artefacts back at the customer while never
    opening the documents the customer actually submitted. Those are the most
    quotable evidence in the engagement — "your privacy policy says X" lands
    where "T08 records X" does not.
    """
    return (f"{bundle['subject']} — the provider's own documentation of this, "
            f"and any policy, procedure or record bearing on {bundle['article']}")


async def write_article_section(agent: Any, bundle: dict[str, Any],
                                rag: Any = None,
                                engagement_id: str = "") -> dict[str, Any]:
    """Compose one article's section of the brief.

    Falls back to a deterministic section built from the bundle when the call
    fails or answers off-contract, so every audited article appears in the
    brief even when the model does not answer for it.

    :param agent: The calling :class:`ClientBriefAgent`.
    :param bundle: The article's evidence bundle from :mod:`.bundle`.
    :param rag: A ``RegulatoryRAG`` instance, or ``None``.
    :returns: The section payload, carrying ``article``, ``verdict`` and
        ``llm_written`` alongside whichever prose keys were produced.
    """
    article = bundle["article"]
    try:
        payload = await acompletion_json_react(
            agent, PROMPT_NAME,
            {"task": f"Explain to the customer what this audit concluded about "
                     f"{article} ({bundle['subject']}) and why.",
             "article_bundle": bundle,
             "regulatory_hits": seed_regulatory_hits(rag, _anchor_query(article)),
             "client_doc_hits": seed_client_doc_hits(engagement_id, _doc_query(bundle))},
            contract=_CONTRACT, rounds=0)
    except Exception as exc:  # noqa: BLE001 — one article must not lose the brief
        logger.warning("Client brief: %s section fell back to the deterministic "
                       "assembly (%s).", article, exc)
        return deterministic_section(bundle)
    section = {k: payload[k] for k in SECTION_KEYS if payload.get(k)}
    return {**section, "article": article, "subject": bundle["subject"],
            "verdict": bundle["verdict"], "llm_written": True}
