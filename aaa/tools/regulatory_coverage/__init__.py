"""KPI 2 — Regulatory Coverage % (§9.1)

Fraction of in-scope EU AI Act articles the audit actually reached a verdict
on. Articles it was unable to assess do not count towards it (finding F13).

  in_scope  = ARTICLE_SET[risk_tier] minus any NOT_APPLICABLE article
  covered   = {a ∈ in_scope : compliance_matrix[a] is a reached conclusion,
               i.e. PASS / PASS_WITH_OBSERVATIONS / FAIL — never
               INSUFFICIENT_EVIDENCE, which means the audit could not assess it}
  pct       = 100 * |covered| / max(|in_scope|, 1)

Written to AuditState.regulatory_coverage_pct."""
from aaa.tools.regulatory_coverage.article_set import (  # noqa: F401
    _ADMITTED_VERDICTS,
    ARTICLE_SET,
    _resolve_article_set,
)
from aaa.tools.regulatory_coverage.compute_regulatory_coverage_pct import (  # noqa: F401
    compute_regulatory_coverage_pct,
)
from aaa.tools.regulatory_coverage.covered_articles import covered_articles  # noqa: F401
from aaa.tools.regulatory_coverage.derive_fallback_verdicts import (  # noqa: F401
    _derive_fallback_verdicts,
)
from aaa.tools.regulatory_coverage.regulatory_coverage_breakdown import (  # noqa: F401
    regulatory_coverage_breakdown,
)

__all__ = [
    'ARTICLE_SET',
    '_ADMITTED_VERDICTS',
    '_resolve_article_set',
    '_derive_fallback_verdicts',
    'compute_regulatory_coverage_pct',
    'covered_articles',
    'regulatory_coverage_breakdown',
]
