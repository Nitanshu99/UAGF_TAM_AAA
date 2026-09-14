"""annex_iv_validator — deterministic MCP-style tool.

Validates a Stage B `AnnexIVDossier` submission against the
`T01b_annex_iv_dossier` JSON Schema (draft-07).

Usage (§4.5):
    result = annex_iv_validator(dossier_dict, declared_modality)

Returns a structured ValidationResult that the Orchestrator / Intake
Validator consumes to gate Phase 1 (must be is_valid=True)."""
from aaa.tools.annex_iv_validator.checks.conditional_fields import (  # noqa: F401
    _check_conditional_fields,
    _format_error,
    annex_iv_validator,
)
from aaa.tools.annex_iv_validator.schema_path import (  # noqa: F401
    _AGENTIC_REQUIRED_FIELDS,
    _L_BRANCH_MODALITIES,
    _L_BRANCH_REQUIRED_FIELDS,
    _SCHEMA_PATH,
    ConditionalFieldStatus,
    FieldError,
)
from aaa.tools.annex_iv_validator.validationresult import ValidationResult  # noqa: F401

__all__ = [
    '_SCHEMA_PATH', '_L_BRANCH_MODALITIES', '_L_BRANCH_REQUIRED_FIELDS', '_AGENTIC_REQUIRED_FIELDS',
    'FieldError', 'ConditionalFieldStatus', 'ValidationResult', '_check_conditional_fields',
    '_format_error', 'annex_iv_validator',
]
