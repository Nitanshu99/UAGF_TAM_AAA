"""
declaration_diff — deterministic MCP-style tool (§4.5, §8.4).

Compares declared values from Stage A against Phase 1 verified values.
Returns a ``declaration_verification`` map:

    {field_name: "match" | "mismatch" | "corrected" | "not_verifiable"}

Semantics (from §3.6, §5.1):
  "match"          — Phase 1 confirms the declared value.
  "mismatch"       — Phase 1 found a different value → triggers HITL (§8.4).
  "corrected"      — Phase 1 adjusted the value but does NOT raise HITL
                     (only used when the correction is minor and the evidence
                     is unambiguous, e.g. section number mapping).
  "not_verifiable" — Insufficient evidence to confirm or refute.

Any field with ``"mismatch"`` in the returned dict must be raised as a HITL
trigger by the Orchestrator before the final CSP plan is accepted (§6.2 #8).

Usage::

    diff = declaration_diff(declared, verified)
    mismatches = [f for f, v in diff.items() if v == "mismatch"]
"""
from __future__ import annotations

from typing import Any


# Fields compared in order; order affects T02 / logging readability.
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


def diff_annex_iii_sections(
    declared_sections: list[str],
    verified_sections: list[str],
) -> dict[str, str]:
    """
    Lightweight diff for the Annex III section lists.

    Each section gets a verdict:
      "match"          — in both declared and verified
      "mismatch"       — in declared but NOT confirmed (not same as rejected)
      "phase1_added"   — in verified but not declared
      "not_verifiable" — in declared but Phase 1 could not assess

    Note: provenance is the authoritative record (on each AnnexIIIEntry);
    this function returns a compact summary for T02's declaration_verification.

    Parameters
    ----------
    declared_sections : list[str]
        Annex III section numbers declared in Stage A.
    verified_sections : list[str]
        Annex III section numbers confirmed by Phase 1.

    Returns
    -------
    dict[str, str]
        Keyed by ``"annex_iii_§{section}"``.
    """
    result: dict[str, str] = {}
    declared_set = set(declared_sections)
    verified_set = set(verified_sections)

    for section in declared_set | verified_set:
        key = f"annex_iii_§{section}"
        if section in declared_set and section in verified_set:
            result[key] = "match"
        elif section in declared_set and section not in verified_set:
            result[key] = "mismatch"
        else:
            result[key] = "not_verifiable"

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(value: Any) -> Any:
    """Normalise a value for comparison (strings lowercased; others as-is)."""
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return sorted(str(v).strip().lower() for v in value)
    return value
