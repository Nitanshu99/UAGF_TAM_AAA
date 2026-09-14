"""A material defect disputing the engagement's own binding_articles list is unfounded.

T14 states which articles the self-assessment maps that are not among the engagement's
``binding_articles`` — list membership, computed from the list the Verifier is given.
The fresh-clone rehearsal of case 06 (2026-09-14) had the Verifier call that statement
factually incorrect — the articles it names "ARE in binding_articles" — as a *material*
defect; the list in the same request held none of them, and T14 went unadmitted. The
matched runs raised the same claim as not material (T-20260915-001).
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.phases.verification.provider_findings.cited import referenced_articles
from aaa.agents.tier1.phases.verification.unfounded.uncontracted import field_root
from aaa.tools.regulatory_coverage.binding import binding_articles, binds
from aaa.tools.regulatory_coverage.unbound_note import stated_unbound


def scope_refuted_reason(issue: dict[str, Any], content: Any, state: dict[str, Any]) -> str | None:
    """Why *issue* is refuted by ``binding_articles``, or ``None`` when it is not.

    Refuted only when the issue is about binding articles, is raised on the field that
    carries the membership statement, names only articles that statement lists, and the
    engagement's list binds none of the statement's articles.

    :param issue: A material artefact-defect issue.
    :param content: The artefact under review.
    :param state: The AuditState the dispatched ``binding_articles`` are computed from.
    """
    root = field_root(issue.get("field"))
    text = content.get(root) if isinstance(content, dict) else None
    stated = stated_unbound(text if isinstance(text, str) else "")
    listed = binding_articles(state)
    words = f"{issue.get('field') or ''} {issue.get('description') or ''}"
    named = list(issue.get("articles") or []) or referenced_articles(words)
    if (not stated or listed is None or "binding" not in words.lower() or not named
            or not set(named) <= set(stated)):
        return None
    scope = {"binding_articles": listed}
    if any(binds(scope, article) for article in stated):
        return None
    return (f"it disputes {root}'s statement that {', '.join(named)} are not among "
            f"binding_articles, and the engagement's binding_articles ({', '.join(listed)}) "
            "contain none of them")


__all__ = ["scope_refuted_reason"]
