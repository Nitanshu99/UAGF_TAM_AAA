"""Which of T15's articles bind the engagement, and the block for one that does not.

Case 02 (limited risk, 2026-09-13) had Art. 12, 17 and 72 — obligations of
high-risk systems — graded PASS_WITH_OBSERVATIONS; the Verifier refused T15 and
Phase 5's evidence was excluded. The engagement scope already says what binds
(:mod:`aaa.tools.regulatory_coverage.engagement_scope`); T15 now follows it.
An unknown tier keeps every article graded, the conservative reading.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.regulatory_coverage.binding import binds, scope_known

#: T15 block → the article it grades.
BLOCKS = {"art12_record_keeping": "Art.12", "art17_qms": "Art.17",
          "art72_post_market_plan": "Art.72"}


def unbound_blocks(scope: dict[str, Any] | None) -> set[str]:
    """The T15 blocks whose article does not bind an engagement with *scope*.

    :param scope: ``{risk_tier, binding_articles}`` as dispatched, or a state-like dict with a tier.
    """
    if not scope or not scope_known(scope):
        return set()
    return {block for block, article in BLOCKS.items() if not binds(scope, article)}


def not_applicable(block: dict[str, Any], article: str, tier: str) -> dict[str, Any]:
    """*block* restated as not applicable, keeping its evidence references.

    :param block: The graded T15 block.
    :param article: The article it grades.
    :param tier: The engagement's risk tier.
    """
    number = article.replace("Art.", "Art. ")
    return {**block, "status": "NOT_APPLICABLE",
            "rationale": (f"{number} is an obligation of high-risk AI systems; this engagement's "
                          f"risk tier is '{tier}', so it is not assessed as a requirement. The "
                          "provider's documentation is still recorded in the evidence sections.")}
