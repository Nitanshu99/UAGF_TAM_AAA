"""Part 3 of the former ``annex_iv_validator`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from jsonschema import Draft7Validator, ValidationError

from aaa.tools.annex_iv_validator.checks.model_meta import check_model_meta
from aaa.tools.annex_iv_validator.schema_path import (  # noqa: F401
    _AGENTIC_REQUIRED_FIELDS,
    _L_BRANCH_MODALITIES,
    _L_BRANCH_REQUIRED_FIELDS,
    _SCHEMA_PATH,
    _T01B_SCHEMA,
    ConditionalFieldStatus,
    FieldError,
)
from aaa.tools.annex_iv_validator.validationresult import ValidationResult  # noqa: F401


def _check_conditional_fields(result: ValidationResult, dossier: dict[str, Any],
                              declared_modality: str) -> None:
    """Record L-branch / agentic conditional-field statuses on *result*.

    :param result: Validation result mutated in place.
    :param dossier: Raw Stage B dossier.
    :param declared_modality: Modality declared in Stage A.
    """
    checks = [
        (_L_BRANCH_REQUIRED_FIELDS, declared_modality in _L_BRANCH_MODALITIES,
         f"declared_modality in {sorted(_L_BRANCH_MODALITIES)}", False),
        (_AGENTIC_REQUIRED_FIELDS, declared_modality == "agentic",
         "declared_modality == 'agentic'", True),
    ]
    for fields, applicable, condition, truthy in checks:
        for fname in fields:
            value = dossier.get(fname)
            present = bool(value) if truthy else (value is not None and value != "")
            result.missing_conditional.append(
                ConditionalFieldStatus(field=fname, condition=condition,
                                       applicable=applicable, present=present))
            if applicable and not present:
                result.is_valid = False


def _format_error(error: ValidationError) -> str:
    path = " → ".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"


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
    _check_conditional_fields(result, dossier, declared_modality)

    # 3. S6 model-meta statuses — surfaced as findings, never invalidating.
    check_model_meta(result, dossier)
    return result
