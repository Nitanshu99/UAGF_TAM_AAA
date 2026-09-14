"""Per-section field derivations for the S5 dialect (see :mod:`aaa.tools.cgsa_ingest.s5.dialect`).

Every function here fills fields the pinned contract requires and the dialect
omits, and each derives its value from data the payload already carries. None
invents: where a value cannot be derived it is left absent, so schema validation
still reports it rather than accepting a placeholder as governance evidence.
"""
from __future__ import annotations

from aaa.tools.cgsa_ingest.s5.fields.controls import (
    article_of,
    articles_of,
    control_summary,
    controls_by_id,
    gap_text,
)
from aaa.tools.cgsa_ingest.s5.fields.coverage import article_control_ids, coverage_pct
from aaa.tools.cgsa_ingest.s5.fields.findings import (
    actions_by_control,
    constraint_fields,
    finding_fields,
    low_confidence_reason,
)
from aaa.tools.cgsa_ingest.s5.fields.positive import positive_findings

__all__ = ["actions_by_control", "article_control_ids", "article_of", "articles_of",
           "constraint_fields", "control_summary", "controls_by_id", "coverage_pct",
           "finding_fields", "gap_text", "low_confidence_reason", "positive_findings"]
