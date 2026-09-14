"""Part 2 of the former ``triage_render`` module (auto-split)."""
from __future__ import annotations

from typing import Any

import jsonschema
from jsonschema import Draft7Validator

from aaa.tools.scope_gate import scope_gate
from aaa.tools.triage_render.schema_path import (  # noqa: F401
    _ANNEX_III_LABELS,
    _MODALITY_LABELS,
    _RISK_TIER_LABELS,
    _SCHEMA_PATH,
    _T01A_SCHEMA,
    TriageRenderResult,
)


def _fmt(error: jsonschema.ValidationError) -> str:
    path = " → ".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"


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
        "scope_gate": scope_gate(payload).to_dict(),
        "schema_version": _T01A_SCHEMA.get("$id", "unknown"),
    }

    result.rendered = rendered
    return result
