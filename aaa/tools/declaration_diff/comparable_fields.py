"""Part 1 of the former ``declaration_diff`` module (auto-split)."""
from __future__ import annotations

from typing import Any

_COMPARABLE_FIELDS: list[str] = [
    "modality",
    "risk_tier",
    "deployment_context",
    "is_llm_or_agentic",
    "provider_elects_third_party",
    "gdpr_overlap",
    "special_category_data",
    "gpai_general_purpose",
]


def _normalise(value: Any) -> Any:
    """Normalise a value for comparison (strings lowercased; others as-is)."""
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return sorted(str(v).strip().lower() for v in value)
    return value
