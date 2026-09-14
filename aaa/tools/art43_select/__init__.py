"""art43_select — deterministic MCP-style tool (§3.5, §4.5).

Implements the Article 43 conformity-assessment procedure selector.
Runs TWICE per engagement:

  1. **Preview** — at Stage A submission, from *declared* values.
     Written to T01a.art43_preview.
  2. **Final**   — after Phase 1 verification, from *verified* values.
     Written to T05_art43_decision and AuditState.art43_decision.

Any difference between preview and final is recorded in T01c and raised
as a HITL "declaration mismatch" trigger (§8.4).

Reference implementation of the rule table from §3.5 of ARCHITECTURE.md."""
from aaa.tools.art43_select.art43_select_from_state import art43_select_from_state  # noqa: F401
from aaa.tools.art43_select.art43selectinput import (  # noqa: F401
    Art43SelectInput,
    _non_high_risk_decision,
)
from aaa.tools.art43_select.core import art43_select  # noqa: F401

__all__ = [
    'Art43SelectInput', '_non_high_risk_decision', 'art43_select', 'art43_select_from_state',
]
