"""
annex_iv_validator — deterministic MCP-style tool.

Validates a Stage B `AnnexIVDossier` submission against the
`T01b_annex_iv_dossier` JSON Schema (draft-07).

Usage (§4.5):
    result = annex_iv_validator(dossier_dict, declared_modality)

Returns a structured ValidationResult that the Orchestrator / Intake
Validator consumes to gate Phase 1 (must be is_valid=True).
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

import jsonschema
from jsonschema import Draft7Validator, ValidationError

# Load the JSON Schema once at import time (version-pinned).
_SCHEMA_PATH = pathlib.Path(__file__).parents[2] / "templates" / "T01b_annex_iv_dossier.json"
with _SCHEMA_PATH.open() as _f:
    _T01B_SCHEMA: dict[str, Any] = json.load(_f)

# L-branch modalities that require the conditional fields.
_L_BRANCH_MODALITIES = {"llm", "agentic", "gpai"}

# Conditional fields required for L-branch modalities.
_L_BRANCH_REQUIRED_FIELDS = [
    "system_prompt_uri",
    "rag_manifest_uri",
    "guardrail_config_uri",
    "golden_set_uri",
]

# Conditional field required only for agentic modality.
_AGENTIC_REQUIRED_FIELDS = ["tool_inventory"]


@dataclass
class FieldError:
    field: str
    section: int
    reason: str


@dataclass
class ConditionalFieldStatus:
    field: str
    condition: str
    applicable: bool
    present: bool


@dataclass
class ValidationResult:
    """Output contract for annex_iv_validator."""
    is_valid: bool
    schema_errors: list[str] = field(default_factory=list)
    missing_required: list[FieldError] = field(default_factory=list)
    missing_conditional: list[ConditionalFieldStatus] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "schema_errors": self.schema_errors,
            "missing_required": [
                {"field": e.field, "section": e.section, "reason": e.reason}
                for e in self.missing_required
            ],
            "missing_conditional": [
                {
                    "field": c.field,
                    "condition": c.condition,
                    "applicable": c.applicable,
                    "present": c.present,
                }
                for c in self.missing_conditional
            ],
        }


def annex_iv_validator(
    dossier: dict[str, Any],
    declared_modality: str,
) -> ValidationResult:
    """
    Validates the Stage B AnnexIVDossier against the T01b JSON Schema.

    Args:
        dossier: Raw dict matching AnnexIVDossier structure.
        declared_modality: The modality declared in Stage A triage.

    Returns:
        ValidationResult with is_valid=True only if schema passes
        AND all applicable conditional fields are present.
    """
    result = ValidationResult(is_valid=True)

    # 1. JSON-Schema validation (draft-07).
    validator = Draft7Validator(_T01B_SCHEMA)
    errors = sorted(validator.iter_errors(dossier), key=str)
    if errors:
        result.is_valid = False
        result.schema_errors = [_format_error(e) for e in errors]

    # 2. Conditional field checks for L-branch modalities.
    is_l_branch = declared_modality in _L_BRANCH_MODALITIES
    is_agentic = declared_modality == "agentic"

    for fname in _L_BRANCH_REQUIRED_FIELDS:
        value = dossier.get(fname)
        present = value is not None and value != ""
        applicable = is_l_branch
        result.missing_conditional.append(
            ConditionalFieldStatus(
                field=fname,
                condition=f"declared_modality in {sorted(_L_BRANCH_MODALITIES)}",
                applicable=applicable,
                present=present,
            )
        )
        if applicable and not present:
            result.is_valid = False

    for fname in _AGENTIC_REQUIRED_FIELDS:
        value = dossier.get(fname)
        present = bool(value)
        applicable = is_agentic
        result.missing_conditional.append(
            ConditionalFieldStatus(
                field=fname,
                condition="declared_modality == 'agentic'",
                applicable=applicable,
                present=present,
            )
        )
        if applicable and not present:
            result.is_valid = False

    return result


def _format_error(error: ValidationError) -> str:
    path = " → ".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"
