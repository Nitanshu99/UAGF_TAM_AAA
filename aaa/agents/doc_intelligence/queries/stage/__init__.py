"""Per-stage field queries for the document-intelligence extractor.

``a`` holds the Stage A fields and queries, ``b`` the Stage B queries; the
parent package combines them into ``FIELD_QUERIES``.
"""
from __future__ import annotations

from aaa.agents.doc_intelligence.queries.stage.a import STAGE_A_FIELDS, STAGE_A_QUERIES
from aaa.agents.doc_intelligence.queries.stage.b import STAGE_B_QUERIES

__all__ = ["STAGE_A_FIELDS", "STAGE_A_QUERIES", "STAGE_B_QUERIES"]
