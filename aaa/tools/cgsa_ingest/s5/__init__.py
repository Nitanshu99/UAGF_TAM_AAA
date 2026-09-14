"""The S5 (evaluated) CGSA export dialect: detection and adaptation (``dialect``) and the per-control field readers (``fields``)."""
from __future__ import annotations

from aaa.tools.cgsa_ingest.s5.dialect import S5_DIALECT_PREFIX, adapt_s5_dialect, is_s5_dialect
from aaa.tools.cgsa_ingest.s5.fields import (
    actions_by_control,
    article_control_ids,
    article_of,
    articles_of,
    constraint_fields,
    control_summary,
    controls_by_id,
    coverage_pct,
    finding_fields,
    gap_text,
    low_confidence_reason,
)

__all__ = ["S5_DIALECT_PREFIX", "is_s5_dialect", "adapt_s5_dialect", "controls_by_id", "articles_of", "article_of", "gap_text", "control_summary", "actions_by_control", "finding_fields", "constraint_fields", "low_confidence_reason", "article_control_ids", "coverage_pct"]
