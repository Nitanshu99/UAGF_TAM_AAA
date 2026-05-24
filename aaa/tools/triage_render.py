"""
triage_render — deterministic MCP-style tool (§4.5).

Validates a Stage A triage payload against the T01a JSON Schema (draft-07)
and renders it to a human-readable dict / JSON string suitable for the
Intake Validator, the Orchestrator, and the wizard UI.

Does NOT write to the Evidence Store — that is the IntakeValidator's job.

Usage:
    result = triage_render(payload_dict)
    if result.is_valid:
        rendered = result.rendered
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

import jsonschema
from jsonschema import Draft7Validator

_SCHEMA_PATH = pathlib.Path(__file__).parents[1] / "templates" / "T01a_stage_a_triage.json"
with _SCHEMA_PATH.open() as _f:
    _T01A_SCHEMA: dict[str, Any] = json.load(_f)

# Human-readable section labels for the wizard display.
_ANNEX_III_LABELS: dict[str, str] = {
    "1": "Biometrics (remote ID, categorisation, emotion recognition)",
    "2": "Critical infrastructure (energy, water, traffic)",
    "3": "Education and vocational training",
    "4": "Employment, workers management, self-employment",
    "5": "Access to essential private/public services",
    "6": "Law enforcement",
    "7": "Migration, asylum, border control",
    "8": "Administration of justice and democratic processes",
}

_MODALITY_LABELS: dict[str, str] = {
    "tabular": "Tabular / structured data classifier",
    "cv": "Computer vision",
    "nlp": "Natural language processing",
    "time_series": "Time-series / forecasting",
    "llm": "Large Language Model (LLM)",
    "agentic": "Agentic AI system (tool-using)",
    "gpai": "General-Purpose AI (GPAI) model",
}

_RISK_TIER_LABELS: dict[str, str] = {
    "high": "High-risk (Annex III)",
    "limited": "Limited risk (Art. 50 transparency obligations)",
    "minimal": "Minimal / no risk",
    "gpai": "General-Purpose AI (Arts. 51–55)",
}


@dataclass
class TriageRenderResult:
    """Output contract for triage_render."""
    is_valid: bool
    schema_errors: list[str] = field(default_factory=list)
    rendered: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "schema_errors": self.schema_errors,
            "rendered": self.rendered,
        }


def triage_render(payload: dict[str, Any]) -> TriageRenderResult:
    """
    Validates and renders a Stage A triage payload.

    Args:
        payload: Raw dict matching StageATriage / T01a schema.

    Returns:
        TriageRenderResult.  If is_valid is True, .rendered contains
        a human-annotated version of the payload ready for the wizard UI
        and for writing to the Evidence Store as T01a.
    """
    result = TriageRenderResult(is_valid=True)

    # 1. Schema validation.
    validator = Draft7Validator(_T01A_SCHEMA)
    errors = sorted(validator.iter_errors(payload), key=str)
    if errors:
        result.is_valid = False
        result.schema_errors = [_fmt(e) for e in errors]
        return result

    # 2. Annotate with human-readable labels.
    declared_sections = payload.get("declared_annex_iii_sections", [])
    rendered: dict[str, Any] = {
        **payload,
        "declared_modality_label": _MODALITY_LABELS.get(
            payload.get("declared_modality", ""), payload.get("declared_modality", "")
        ),
        "declared_risk_tier_label": _RISK_TIER_LABELS.get(
            payload.get("declared_risk_tier", ""), payload.get("declared_risk_tier", "")
        ),
        "declared_annex_iii_labels": [
            f"§{s} — {_ANNEX_III_LABELS.get(s, s)}" for s in declared_sections
        ],
        "is_l_branch": payload.get("declared_modality") in {"llm", "agentic", "gpai"},
        "triggers_privacy_tier3": (
            payload.get("gdpr_overlap", False)
            or payload.get("special_category_data", False)
        ),
        "triggers_gpai_module": payload.get("gpai_general_purpose", False),
        "schema_version": _T01A_SCHEMA.get("$id", "unknown"),
    }

    result.rendered = rendered
    return result


def _fmt(error: jsonschema.ValidationError) -> str:
    path = " → ".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"
