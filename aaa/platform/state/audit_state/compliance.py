"""Compliance-assembly section of the :class:`AuditState` TypedDict."""
from __future__ import annotations

from typing import Any, NotRequired, Optional, TypedDict

from aaa.platform.state.cgsa import RemediationItem
from aaa.platform.state.findings import Article, Finding, Verdict
from aaa.platform.state.verdicts import FinalVerdict


class AuditStateCompliance(TypedDict):
    """Compliance assembly, verification, and final verdict fields."""
    compliance_matrix: dict[Article, Verdict]
    blocking_findings: list[Finding]
    positive_findings: list[Finding]
    remediation_roadmap: list[RemediationItem]
    material_findings_count: Optional[int]
    possibly_material_findings_count: Optional[int]
    # Articles whose required independent analysis could not be performed (missing
    # artefact, unscored eval set, agent fallback). Accumulated across phases; the
    # compliance matrix marks these INSUFFICIENT_EVIDENCE (never PASS). (§WS5/WS8)
    insufficient_evidence_articles: NotRequired[list[str]]
    # Phases that closed below the confidence floor, with the articles each one
    # therefore contributed to ``insufficient_evidence_articles`` (F5). Recorded
    # so a disclaimer traceable to self-reported doubt can be read as such.
    low_confidence_phases: NotRequired[list[dict[str, Any]]]
    # Procedure id → {outcome, reason}, from each phase's delta; and the scope
    # limitations the audit programme derives from them before verdicts are set.
    procedure_outcomes: NotRequired[dict[str, dict[str, Any]]]
    scope_limitations: NotRequired[list[dict[str, Any]]]
    # Artefacts the Verifier did not admit — critique never ran (``unverified``),
    # or ran and rejected (``rerun`` / ``escalate_hitl``) — each with its verdict
    # and the reason (P6/Q1). Their articles are in
    # ``insufficient_evidence_articles`` for the same reason a low-confidence
    # phase's are: nothing admitted as evidence assessed them.
    unadmitted_artefacts: NotRequired[list[dict[str, Any]]]
    verifier_critiques: dict[str, dict[str, Any]]
    # Human-review escalation. Set by ``verification.finish_phase`` (and by the
    # phase agents' deltas) and read by the Orchestrator's ReAct envelope, the
    # HITL review packet and the report front matter.
    hitl_required: NotRequired[bool]
    hitl_reason: NotRequired[Optional[str]]
    # Append-only record of Orchestrator ESCALATE_HITL alerts (F8). Kept
    # separately because ``hitl_reason`` is assigned by many writers and the
    # next escalating phase overwrites whatever the Orchestrator recorded.
    hitl_alerts: NotRequired[list[str]]
    # Compact views of the most recent phase Report and its Verifier critique,
    # written by ``verification.phase_outcome`` for the Orchestrator's next
    # observation — the phase runners themselves discard the Report. (F3)
    latest_report: NotRequired[Optional[dict[str, Any]]]
    latest_critique: NotRequired[Optional[dict[str, Any]]]
    # ReAct control-loop trail. ``react_termination`` is set only when the
    # loop ended in the deterministic wrap-up rather than a model FINALIZE,
    # which the output could not previously distinguish. (F12)
    react_decision_history: NotRequired[list[dict[str, Any]]]
    react_termination: NotRequired[Optional[dict[str, Any]]]
    intake_completeness_score: Optional[float]
    completeness_score: Optional[float]
    regulatory_coverage_pct: Optional[float]
    # ``DISCLAIMER_OF_OPINION`` is the engagement-level counterpart of an
    # article's INSUFFICIENT_EVIDENCE: the audit could not obtain the evidence
    # to conclude. Without it, an unassessable engagement had to borrow
    # PASS_WITH_OBSERVATIONS and contradict its own auditor_opinion (F11).
    final_verdict: Optional[FinalVerdict]
    auditor_opinion: Optional[dict]
