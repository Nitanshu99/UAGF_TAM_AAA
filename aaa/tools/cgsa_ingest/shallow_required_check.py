"""Part 2 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.logger import (  # noqa: F401
    _LOW_CONFIDENCE_THRESHOLD,
    _REQUIRED_TOP_LEVEL_KEYS,
    _VENDORED_SCHEMA,
    CGSAIngestError,
    IngestResult,
    logger,
)


def _shallow_required_check(payload: dict[str, Any]) -> list[str]:
    """Minimal fallback when ``jsonschema`` is not installed."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"missing required top-level key: {key}")
    handoff = payload.get("aaa_phase5_handoff", {})
    for key in (
        "phase5_verdict", "phase5_narrative_summary", "blocking_findings_count",
        "blocking_findings", "positive_findings", "low_confidence_controls",
        "aaa_recommended_follow_up",
    ):
        if key not in handoff:
            errors.append(f"missing required aaa_phase5_handoff key: {key}")
    return errors
