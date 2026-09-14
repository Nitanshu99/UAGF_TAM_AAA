"""Remediation-roadmap section builder for T14.

The T14 schema describes this section as the *verbatim* CGSA roadmap and forbids
any other key. It was built from the enriched state list instead: every
``control_name`` came out empty because ingest had dropped it, the required
``action`` and ``eu_ai_act_article`` were missing, and five enrichment keys the
schema forbids were added — 108 schema errors on the 36-row case-06 roadmap
(T-20260913-007). Owner, priority and deadline are the auditor's additions; they
stay in state for T18 and do not belong in a copy of the source of record.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest import IngestResult

#: The T14 severity enum, plus the legacy dialect older CGSA payloads use.
_SEVERITY = {"critical": "critical", "high": "high", "medium": "medium", "low": "low",
             "major": "high", "minor": "medium", "observation": "low"}
_EFFORT = frozenset({"low", "medium", "high"})


def _whole(value: Any) -> int | None:
    """An integer score or week count, or ``None`` — never a guessed ``0``."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _row(item: dict[str, Any], idx: int) -> dict[str, Any]:
    """One roadmap row in exactly the T14 schema's fields."""
    effort = str(item.get("effort_estimate") or "").lower()
    return {
        "rank": _whole(item.get("rank")) or idx + 1,
        "control_id": str(item.get("control_id") or ""),
        "control_name": str(item.get("control_name") or ""),
        "gap_severity": _SEVERITY.get(str(item.get("gap_severity") or "").lower(), "medium"),
        "current_score": _whole(item.get("current_score")),
        "target_score": _whole(item.get("target_score")),
        "action": str(item.get("action") or item.get("recommended_action") or ""),
        "eu_ai_act_article": str(item.get("eu_ai_act_article") or ""),
        "effort_estimate": effort if effort in _EFFORT else None,
        "timeline_weeks": _whole(item.get("timeline_weeks")),
    }


def remediation_section(result: IngestResult) -> list[dict[str, Any]]:
    """The CGSA remediation roadmap, copied in the source's order.

    :param result: Validated CGSA ingest result.
    :returns: Rows carrying only the fields the T14 schema allows.
    """
    payload = result.payload if isinstance(result.payload, dict) else {}
    rows = payload.get("remediation_roadmap") or result.state_delta.get(
        "remediation_roadmap") or []
    return [_row(item, idx) for idx, item in enumerate(rows) if isinstance(item, dict)]
