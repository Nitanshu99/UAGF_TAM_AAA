"""The engagement's binding articles, computed once and carried to every agent that judges scope.

The Verifier judges an artefact against ``engagement_scope.binding_articles`` — the
tier's set plus the Stage A gate's. Phase 5 judged the same question from the
dispatched ``risk_tier`` alone, so a gate-scoped article read as unbound: case 06's
T14 (2026-09-14, evaluated CGSA export) told the Verifier that Art. 50 "does not
bind" an engagement whose binding articles list it, and was refused as a material
contradiction (T-20260914-055). Both sides now read the same list.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.regulatory_coverage.engagement_scope import (
    canonical_article,
    core_article,
    engagement_articles,
    is_in_scope,
    scope_is_known,
)


def binding_articles(state: dict[str, Any]) -> list[str] | None:
    """Every article that binds the engagement, judged at its verified tier once there is one.

    :param state: The AuditState.
    :returns: Sorted article ids, or ``None`` while no tier is known.
    """
    scoped = {**state, "risk_tier": state.get("verified_risk_tier") or state.get("risk_tier")}
    return sorted(engagement_articles(scoped)) if scope_is_known(scoped) else None


def scope_known(scope: dict[str, Any] | None) -> bool:
    """Whether *scope* says what binds: a carried ``binding_articles`` list, or a known tier."""
    return bool(scope) and (scope.get("binding_articles") is not None or scope_is_known(scope))


def binds(scope: dict[str, Any], article: str) -> bool:
    """Whether *article* — or the article it is a sub-article of — binds the engagement.

    :param scope: ``{binding_articles}`` as dispatched, or a state-like dict with a tier.
    :param article: An article reference (``Art.50``, ``Art.10§5``).
    """
    listed = scope.get("binding_articles")
    if listed is None:
        return is_in_scope(scope, article)
    return (canonical_article(article) in listed
            or canonical_article(core_article(article)) in listed)


__all__ = ["binding_articles", "binds", "scope_known"]
