"""T17 compliance-matrix payload builder.

**Finding Q5 — the deliverable under-declared its own scope.** ``in_scope_articles``
was built from ``sorted(compliance_matrix.keys())``, so it reported whatever the
matrix happened to hold: 13 entries on an engagement whose article set holds 15.
The schema has always said the field comes from ``regulatory_coverage.ARTICLE_SET``
and that ``articles`` carries *"one row per in-scope article"*, and KPI 2 has
always counted against that set — so the delivered document presented a
13-article audit as complete beside a coverage figure computed over 15.

Both now come from the one resolution KPI 2 uses, and a row is emitted for every
in-scope article. An article no phase reached is therefore *visible* — printed as
``INSUFFICIENT_EVIDENCE`` with a rationale saying so — rather than silently
missing from the client's conformity table. That is deliberately a second line of
defence behind fix 26: Q1's articles vanished because one gate did not cover a
verdict, and a table that only prints what it was handed cannot show the reader
what it was never handed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aaa.agents.tier2.report_architect.t17_rows import _article_row
from aaa.platform.state.verdicts import DISCLAIMER_OF_OPINION
from aaa.tools.regulatory_coverage.article_set import _resolve_article_set

if TYPE_CHECKING:
    from aaa.platform.state import AuditState





def build_t17(engagement_id: str, decl: dict[str, Any], now: str) -> dict[str, Any]:
    """Build the T17 compliance matrix from the orchestrator state.

    :param engagement_id: Engagement identifier.
    :param decl: Declaration summary carrying matrix, findings and KPIs.
    :param now: ISO-8601 generation timestamp.
    :returns: T17 compliance-matrix dictionary.
    """
    compliance_matrix: dict[str, str] = decl.get("compliance_matrix", {}) or {}
    article_evidence: dict[str, Any] = decl.get("article_evidence", {}) or {}
    risk_tier: str = decl.get("risk_tier", "high")

    # The same resolution KPI 2 uses, off the same fields — so the article list
    # and the coverage percentage beside it cannot describe different audits (Q5).
    # The declaration summary carries `risk_tier` and `is_llm_or_agentic`, which
    # is everything the resolution reads; the cast is the one the graph nodes use.
    in_scope = set(_resolve_article_set(cast("AuditState", decl)))
    # In-scope articles the matrix missed get a row; sub-articles the matrix
    # holds (`Art.10§2(f)`) are not in ARTICLE_SET and keep theirs.
    rows = [_article_row(article, compliance_matrix, article_evidence)
            for article in sorted(in_scope | set(compliance_matrix))]

    hitl_pending = bool(decl.get("hitl_required", False))
    return {
        "engagement_id": engagement_id,
        "risk_tier": risk_tier if risk_tier != "prohibited" else "high",
        "is_llm_or_agentic": bool(decl.get("is_llm_or_agentic", False)),
        "in_scope_articles": sorted(in_scope),
        "articles": rows,
        "kpi_summary": {
            "intake_completeness_score": decl.get("intake_completeness_score"),
            "completeness_score": decl.get("completeness_score"),
            "regulatory_coverage_pct": decl.get("regulatory_coverage_pct"),
        },
        "blocking_findings_count": len(decl.get("blocking_findings", []) or []),
        "final_verdict": decl.get("final_verdict") or DISCLAIMER_OF_OPINION,
        "report_status": "PROVISIONAL_PENDING_HITL" if hitl_pending else "FINAL",
        "hitl_pending": hitl_pending,
        "generated_at": now,
    }
