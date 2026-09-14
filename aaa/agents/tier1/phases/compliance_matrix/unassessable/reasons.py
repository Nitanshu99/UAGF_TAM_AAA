"""Why an in-scope article can never be evidenced by this engagement's own artefacts."""
from __future__ import annotations

from aaa.agents.tier1.phases.compliance_matrix.logger import _TEMPLATE_ARTICLES
from aaa.tools.regulatory_coverage.engagement_scope import (
    canonical_article,
    core_article,
    engagement_articles,
    scope_is_known,
)
from aaa.tools.regulatory_coverage.ownership import article_owners, is_schedulable
from aaa.tools.regulatory_coverage.unowned import KNOWN_UNOWNED


def _diagnosable(state: dict, matrix_keys: set[str]) -> set[str]:
    """In-scope articles worth diagnosing: every one except an aliased duplicate.

    An article that *is* a row is still worth diagnosing — case 04's Art. 50 is
    listed because the scope gate raised it, and "nothing can evidence it" is a
    different and stronger fact than "nothing did". An article that is not a row
    but whose canonical form is one under another spelling is already covered,
    and diagnosing it would report `GPAI_51` unassessable while `Art.51` passes.
    """
    if not scope_is_known(state):
        return set()
    canonical_rows = {canonical_article(core_article(k)) for k in matrix_keys}
    return {a for a in engagement_articles(state)
            if a in matrix_keys
            or canonical_article(core_article(a)) not in canonical_rows}


def unassessable_reasons(state: dict) -> dict[str, str]:
    """In-scope articles no artefact this engagement will produce can evidence.

    :param state: The AuditState dict, carrying ``phase_plan`` when the CSP ran.
    :returns: ``{article: why}``, sorted by article.
    """
    plan = state.get("phase_plan") or {}
    out: dict[str, str] = {}
    for article in sorted(_diagnosable(state, set(state.get("compliance_matrix") or {}))):
        owners = article_owners(article, _TEMPLATE_ARTICLES)
        if not owners:
            out[article] = KNOWN_UNOWNED.get(
                article, "no artefact in the catalogue evidences this article")
        elif plan and not is_schedulable(article, plan, _TEMPLATE_ARTICLES):
            out[article] = (
                f"its evidence comes from {', '.join(sorted(owners))}, and this "
                f"engagement's plan does not schedule "
                f"{', '.join(f'{p}={plan.get(p, chr(63))}' for p in sorted(owners))}")
    return out


__all__ = ["unassessable_reasons"]
