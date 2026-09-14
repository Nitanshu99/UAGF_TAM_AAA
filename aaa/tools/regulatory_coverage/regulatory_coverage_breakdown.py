"""Part 4 of the former ``regulatory_coverage`` module (auto-split)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from aaa.tools.regulatory_coverage.article_set import (  # noqa: F401
    _ADMITTED_VERDICTS,
    ARTICLE_SET,
    _resolve_article_set,
)
from aaa.tools.regulatory_coverage.compute_regulatory_coverage_pct import (  # noqa: F401
    compute_regulatory_coverage_pct,
)
from aaa.tools.regulatory_coverage.covered_articles import covered_articles
from aaa.tools.regulatory_coverage.derive_fallback_verdicts import (  # noqa: F401
    _derive_fallback_verdicts,
)

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def regulatory_coverage_breakdown(state: AuditState) -> dict:
    """
    Return a per-article breakdown for T17/T18 report embedding.

    Shares :func:`covered_articles` with KPI 2 itself, so ``missing`` always
    names exactly the articles the percentage docks the audit for.

    Returns
    -------
    dict with keys:
        regulatory_coverage_pct  – overall KPI 2 float
        in_scope                 – sorted list of article IDs
        covered                  – sorted list of covered article IDs
        missing                  – sorted list of uncovered article IDs
    """
    return covered_articles(state)
