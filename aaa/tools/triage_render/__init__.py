"""triage_render — deterministic MCP-style tool (§4.5).

Validates a Stage A triage payload against the T01a JSON Schema (draft-07)
and renders it to a human-readable dict / JSON string suitable for the
Intake Validator, the Orchestrator, and the wizard UI.

Does NOT write to the Evidence Store — that is the IntakeValidator's job.

Usage:
    result = triage_render(payload_dict)
    if result.is_valid:
        rendered = result.rendered"""
from aaa.tools.triage_render.fmt import _fmt, triage_render  # noqa: F401
from aaa.tools.triage_render.schema_path import (  # noqa: F401
    _ANNEX_III_LABELS,
    _MODALITY_LABELS,
    _RISK_TIER_LABELS,
    _SCHEMA_PATH,
    _T01A_SCHEMA,
    TriageRenderResult,
)

__all__ = [
    '_SCHEMA_PATH', '_T01A_SCHEMA', '_ANNEX_III_LABELS', '_MODALITY_LABELS', '_RISK_TIER_LABELS',
    'TriageRenderResult', '_fmt', 'triage_render',
]
