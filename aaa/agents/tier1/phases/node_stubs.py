"""
aaa.agents.tier1.phases.node_stubs — Stub node functions for unimplemented phases.

These stubs are used when the real agents are not wired (offline/demo mode).
Each returns a minimal artefact + verifier critique so downstream nodes can proceed.

Exported functions:
  - node_phase1_stub(state)
  - node_route(state)
  - node_parallel_phases_stub(state)
  - node_phase5_stub(state)
  - node_hitl_checkpoint(state, offline)
  - node_phase6_stub(state)
  - should_hitl(state, offline) → str
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"


def _stub_artefact(engagement_id: str, tid: str) -> dict:
    return {"uri": f"mem://{engagement_id}/{tid}", "sha256": "stub", "template_id": tid}


def _stub_critique(note: str) -> dict:
    return {
        "verdict": "accept", "issues": [], "notes": [note],
        "article_citations": [], "rerun_required": False,
    }


def node_phase1_stub(state: dict) -> dict:
    """Phase 1 stub — used when ScopeAgent is not wired."""
    logger.info("Engagement %s: Phase 1 (Scope) — stub", state["engagement_id"])
    for tid in ["T02_system_card", "T03_annex_iii_mapping",
                "T04_risk_tier_decision", "T05_art43_decision"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
        state["verifier_critiques"][tid] = _stub_critique(
            "Phase 1 stub — real ScopeAgent wired in Group 4."
        )
    return state


def node_route(state: dict) -> dict:
    """Route — determines L-branch vs standard branch."""
    state["_branch"] = "l_branch" if state.get("is_llm_or_agentic") else "standard"
    logger.info(
        "Engagement %s routed to %s branch", state["engagement_id"], state["_branch"]
    )
    return state


def node_parallel_phases_stub(state: dict) -> dict:
    """Parallel phases stub — Phases 2–4 or L-branch when agents are not wired."""
    branch = state.get("_branch", "standard")
    tids = (
        ["T16_uagf_tam_l_evidence"]
        if branch == "l_branch"
        else [
            "T06_datasheet_for_datasets", "T07_data_quality_report",
            "T08_special_category_data_log", "T09_model_card",
            "T10_explainability_report", "T11_robustness_report",
            "T12_output_fairness_report", "T13_output_sampling_log",
        ]
    )
    for tid in tids:
        if tid not in state["phase_artefacts"]:
            state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
            state["verifier_critiques"][tid] = _stub_critique(
                f"{tid} stub — real agent wired in Groups 5–7/10."
            )
    return state


def node_phase5_stub(state: dict) -> dict:
    """Phase 5 stub — used when GovernanceAgent is not wired."""
    logger.info("Engagement %s: Phase 5 (Governance) — stub", state["engagement_id"])
    for tid in ["T14_governance_findings", "T15_monitoring_logging_review"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
        state["verifier_critiques"][tid] = _stub_critique(
            "Phase 5 stub — real GovernanceAgent wired in Group 8."
        )
    return state


def node_hitl_checkpoint(state: dict, offline: bool = _OFFLINE) -> dict:
    """HITL checkpoint — auto-approves in offline mode."""
    needs_hitl = state.get("hitl_required") or state.get("final_verdict") == "FAIL"
    if needs_hitl:
        reason = state.get("hitl_reason") or "FAIL verdict or manual escalation"
        if offline:
            logger.warning("HITL required (%s) — auto-approved in offline mode.", reason)
        else:
            logger.warning("HITL required (%s) — pausing for human review.", reason)
    return state


def node_phase6_stub(state: dict) -> dict:
    """Phase 6 stub — used when ReportArchitect is not wired."""
    logger.info("Engagement %s: Phase 6 (Report) — stub", state["engagement_id"])
    for tid in ["T17_compliance_matrix", "T18_audit_report"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
    return state


def should_hitl(state: dict, offline: bool = _OFFLINE) -> str:
    """Edge function: advance to phase_6 or wait at hitl_checkpoint."""
    if state.get("hitl_required") and not offline:
        return "wait_hitl"
    return "phase_6"


__all__ = [
    "node_phase1_stub",
    "node_route",
    "node_parallel_phases_stub",
    "node_phase5_stub",
    "node_hitl_checkpoint",
    "node_phase6_stub",
    "should_hitl",
]
