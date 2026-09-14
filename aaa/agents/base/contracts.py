"""Typed message contracts exchanged between agents (§5.2)."""
from __future__ import annotations

from typing import Any, Literal, NotRequired, Optional, TypedDict


class IntakeDispatch(TypedDict):
    """Dispatch handed to the IntakeValidator at Stage 0."""
    engagement_id: str
    stage_a_uri: str
    stage_b_uri: str
    stage_c_uri: Optional[str]  # Stage C is optional at intake (no live access)
    annex_iv_schema_version: str


class Dispatch(TypedDict):
    """Dispatch handed to a phase agent by the Orchestrator."""
    phase_id: str
    task_brief: str
    evidence_uris: list[str]
    output_contract: str
    declaration_summary: dict[str, Any]
    #: Absent on a first attempt; carries the Verifier critique that ordered a
    #: rerun (see ``verification.rerun_context.build_rerun_context``).
    rerun_context: NotRequired[dict[str, Any] | None]


class Report(TypedDict):
    """Report returned by a phase agent to the Orchestrator."""
    phase_id: str
    artefact_uri: str
    summary: str
    confidence: float
    tool_calls: list[dict[str, Any]]
    declaration_verification_delta: dict[str, Any]
    #: Phase 6 only, and derived by the runtime — never asserted by the model
    #: (see ``report_architect.signing``). Absent on every other phase.
    report_signed: NotRequired[bool]


class Critique(TypedDict):
    """Verifier critique of a produced artefact."""
    phase_id: str
    verdict: Literal["PASS", "FAIL", "NEEDS_REVISION"]
    issues: list[str]
    rerun_required: bool
