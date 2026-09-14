"""Part 3 of the former ``regulatory_coverage`` module (auto-split)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from aaa.tools.regulatory_coverage.article_set import (  # noqa: F401
    _ADMITTED_VERDICTS,
    ARTICLE_SET,
    _resolve_article_set,
)
from aaa.tools.regulatory_coverage.covered_articles import covered_articles
from aaa.tools.regulatory_coverage.derive_fallback_verdicts import (  # noqa: F401
    _derive_fallback_verdicts,
)

if TYPE_CHECKING:
    from aaa.platform.state import AuditState


def compute_regulatory_coverage_pct(state: AuditState) -> float:
    """
    Compute KPI 2 and write it to ``state['regulatory_coverage_pct']``.

    Coverage is the fraction of in-scope articles the audit actually reached a
    conclusion on: an article counts as *covered* when its ``compliance_matrix``
    verdict is one of
    :data:`aaa.platform.state.verdicts.ASSESSED_ARTICLE_VERDICTS`. Presence in it
    is not enough — an ``INSUFFICIENT_EVIDENCE`` article is one the audit was
    unable to assess, and counting it reported 80% coverage on a run that left
    12 of 14 articles unevidenced (finding F13).

    ``NOT_APPLICABLE`` articles leave the denominator entirely: the requirement
    does not bind, so it is neither covered nor an evidence gap.

    Parameters
    ----------
    state : AuditState

    Returns
    -------
    float  in [0.0, 100.0], rounded to one decimal place.
    """
    pct = covered_articles(state)["regulatory_coverage_pct"]
    state["regulatory_coverage_pct"] = pct
    return pct
