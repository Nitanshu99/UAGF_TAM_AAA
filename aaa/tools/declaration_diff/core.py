"""Part 2 of the former ``declaration_diff`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.declaration_diff.comparable_fields import (  # noqa: F401
    _COMPARABLE_FIELDS,
    _normalise,
)


def declaration_diff(
    declared: dict[str, Any],
    verified: dict[str, Any],
) -> dict[str, str]:
    """
    Deep-diff declared vs verified scalar fields.

    Parameters
    ----------
    declared:
        Dict of declared values, typically from ``AuditState`` ``declared_*``
        fields plus Stage A flags. Expected keys (optional keys are tolerated):

        - ``modality``                 (= ``declared_modality``)
        - ``risk_tier``                (= ``declared_risk_tier``)
        - ``deployment_context``
        - ``is_llm_or_agentic``
        - ``provider_elects_third_party``
        - ``gdpr_overlap``
        - ``special_category_data``
        - ``gpai_general_purpose``

    verified:
        Dict of verified values produced by Phase 1 ScopeAgent.  Keys must
        match those in *declared*.  A key absent from *verified* is recorded
        as ``"not_verifiable"``.

    Returns
    -------
    dict[str, str]
        Map of field name → verdict.  Fields present in *verified* but absent
        from *declared* are included with verdict ``"not_verifiable"``.

    Notes
    -----
    ``annex_iii_sections`` diff is intentionally handled separately by
    ``annex_iii_classify`` (provenance field on each ``AnnexIIIEntry``).
    This tool handles scalar fields only.
    """
    result: dict[str, str] = {}

    all_fields = set(_COMPARABLE_FIELDS) | set(declared.keys()) | set(verified.keys())
    # Only include fields that appear in at least one side
    for field in sorted(all_fields):
        if field.startswith("_"):
            continue  # skip private/internal keys

        in_declared = field in declared
        in_verified = field in verified

        if not in_declared and not in_verified:
            continue

        if in_declared and not in_verified:
            result[field] = "not_verifiable"
            continue

        if not in_declared and in_verified:
            # Phase 1 discovered a field the client didn't declare
            result[field] = "not_verifiable"
            continue

        # Both present — compare values
        d_val = _normalise(declared[field])
        v_val = _normalise(verified[field])

        if d_val == v_val:
            result[field] = "match"
        else:
            # Determine whether this is a hard mismatch or a corrected value.
            # A "corrected" verdict is used only when Phase 1 is certain and
            # the correction does not change the risk tier or routing.
            # Conservative default: treat all differences as "mismatch".
            result[field] = "mismatch"

    return result
