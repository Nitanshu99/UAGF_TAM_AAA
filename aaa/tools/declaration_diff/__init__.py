"""declaration_diff — deterministic MCP-style tool (§4.5, §8.4).

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
    mismatches = [f for f, v in diff.items() if v == "mismatch"]"""
from aaa.tools.declaration_diff.comparable_fields import (  # noqa: F401
    _COMPARABLE_FIELDS,
    _normalise,
)
from aaa.tools.declaration_diff.core import declaration_diff  # noqa: F401
from aaa.tools.declaration_diff.diff_annex_iii_sections import diff_annex_iii_sections  # noqa: F401

__all__ = [
    '_COMPARABLE_FIELDS',
    '_normalise',
    'declaration_diff',
    'diff_annex_iii_sections',
]
