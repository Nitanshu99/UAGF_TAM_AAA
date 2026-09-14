"""Part 2 of the former ``reader`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.data import index as idx
from aaa.data.reader.logger import (  # noqa: F401
    _read_json,
    load_artefacts,
    load_audit_result,
    load_compliance_matrix,
    load_engagement,
    load_findings,
    load_intake,
    load_uploaded_files,
    logger,
)


def load_full_result(engagement_id: str) -> dict[str, Any] | None:
    """Return a merged view of all four result files.

    Returns ``None`` if the audit result file is absent (audit not yet run).
    """
    result = load_audit_result(engagement_id)
    if result is None:
        return None
    return {
        **result,
        "artefacts":        load_artefacts(engagement_id),
        "findings":         load_findings(engagement_id),
        "compliance_matrix": load_compliance_matrix(engagement_id),
    }


def list_engagements() -> list[dict[str, Any]]:
    """Return all engagement index summaries, newest-first."""
    return idx.list_all()


def list_results() -> list[dict[str, Any]]:
    """Return index summaries for engagements that have a final verdict."""
    return [
        row for row in idx.list_all()
        if row.get("final_verdict") is not None
    ]


__all__ = [
    "load_engagement",
    "load_intake",
    "load_uploaded_files",
    "load_audit_result",
    "load_artefacts",
    "load_findings",
    "load_compliance_matrix",
    "load_full_result",
    "list_engagements",
    "list_results",
]
