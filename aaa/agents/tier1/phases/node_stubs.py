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


# Articles a stubbed template would have evidenced — used to mark them
# INSUFFICIENT_EVIDENCE so a stub (no real analysis) can never yield PASS.
_STUB_TID_ARTICLES: dict[str, list[str]] = {
    "T02_system_card": ["Art.5", "Art.13"],
    "T03_annex_iii_mapping": ["Art.6", "Annex_III"],
    "T04_risk_tier_decision": ["Art.5", "Art.6"],
    "T05_art43_decision": ["Art.43"],
    "T06_datasheet_for_datasets": ["Art.10"],
    "T07_data_quality_report": ["Art.10"],
    "T08_special_category_data_log": ["Art.10"],
    "T09_model_card": ["Art.13", "Art.15"],
    "T10_explainability_report": ["Art.13"],
    "T11_robustness_report": ["Art.15"],
    "T12_output_fairness_report": ["Art.10§2(f)", "Art.15§1"],
    "T13_output_sampling_log": ["Art.15§1"],
    "T14_governance_findings": ["Art.9", "Art.17"],
    "T15_monitoring_logging_review": ["Art.12", "Art.72"],
    "T16_uagf_tam_l_evidence": ["Art.15", "Art.51", "Art.52", "Art.53", "Art.54", "Art.55"],
}


def _stub_artefact(engagement_id: str, tid: str) -> dict:
    return {"uri": f"mem://{engagement_id}/{tid}", "sha256": "stub", "template_id": tid}


def _stub_critique(note: str) -> dict:
    # accept_with_notes (not accept) makes the stub visibly non-authoritative.
    return {
        "verdict": "accept_with_notes", "issues": [], "notes": [note],
        "article_citations": [], "rerun_required": False,
    }


def _mark_stub_insufficient(state: dict, tid: str) -> None:
    """Record that a stubbed template's articles lack real verification."""
    ie = state.setdefault("insufficient_evidence_articles", [])
    for art in _STUB_TID_ARTICLES.get(tid, []):
        if art not in ie:
            ie.append(art)


def node_phase1_stub(state: dict) -> dict:
    """Phase 1 stub — used when ScopeAgent is not wired."""
    logger.info("Engagement %s: Phase 1 (Scope) — stub", state["engagement_id"])
    for tid in ["T02_system_card", "T03_annex_iii_mapping",
                "T04_risk_tier_decision", "T05_art43_decision"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
        state["verifier_critiques"][tid] = _stub_critique(
            "Phase 1 stub — no real ScopeAgent analysis performed."
        )
        _mark_stub_insufficient(state, tid)
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
                f"{tid} stub — no real agent analysis performed."
            )
            _mark_stub_insufficient(state, tid)
    return state


def node_phase5_stub(state: dict) -> dict:
    """Phase 5 stub — used when GovernanceAgent is not wired."""
    logger.info("Engagement %s: Phase 5 (Governance) — stub", state["engagement_id"])
    for tid in ["T14_governance_findings", "T15_monitoring_logging_review"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
        state["verifier_critiques"][tid] = _stub_critique(
            "Phase 5 stub — no real GovernanceAgent analysis performed."
        )
        _mark_stub_insufficient(state, tid)
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
