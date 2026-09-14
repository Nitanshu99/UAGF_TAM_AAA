"""Part 2 of the former ``annex_iv_validator`` module (auto-split)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aaa.tools.annex_iv_validator.schema_path import (  # noqa: F401
    _AGENTIC_REQUIRED_FIELDS,
    _L_BRANCH_MODALITIES,
    _L_BRANCH_REQUIRED_FIELDS,
    _SCHEMA_PATH,
    ConditionalFieldStatus,
    FieldError,
)


@dataclass
class ValidationResult:
    """Output contract for annex_iv_validator."""
    is_valid: bool
    schema_errors: list[str] = field(default_factory=list)
    missing_required: list[FieldError] = field(default_factory=list)
    missing_conditional: list[ConditionalFieldStatus] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the ValidationResult as a plain dict."""
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
