"""
aaa.agents.tier1.phases.phase_runners — Phase node implementations for the Orchestrator.

Each ``run_phase_N(agent, state)`` function:
  - Builds the Dispatch for that phase
  - Calls ``run_agent_on_state``
  - Returns the updated state (falls through to stub on failure)

Exported functions:
  run_phase_1, run_phase_2, run_phase_3, run_phase_4,
  run_phase_5, run_phase_6, run_uagf_tam_l,
  run_cyber_subagent, run_privacy_subagent
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import run_agent_on_state, _evidence_uris
from aaa.agents.tier1.phases.node_stubs import (
    node_phase1_stub,
    node_parallel_phases_stub,
    node_phase5_stub,
    node_phase6_stub,
)

logger = logging.getLogger(__name__)


async def run_phase_1(agent: Any, state: dict) -> dict:
    """Run ScopeAgent (Phase 1); fall back to stub on error."""
    if agent is None:
        return node_phase1_stub(state)
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="P1",
        task_brief="Verify declared modality, risk tier, and Annex III sections.",
        evidence_uris=_evidence_uris(state),
        output_contract="T02_system_card",
        declaration_summary={
            "engagement_id": eng,
            "client_doc_collection": state.get("client_doc_collection"),
            "declared_modality": state.get("declared_modality", ""),
            "declared_risk_tier": state.get("declared_risk_tier", ""),
            "declared_annex_iii_sections": state.get("declared_annex_iii_sections", []),
            "deployment_context": state.get("deployment_context", ""),
        },
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=120)
    if report is None:
        return node_phase1_stub(state)
    confidence = report.get("confidence", 0.9)
    for tid in ["T02_system_card", "T03_annex_iii_mapping", "T04_risk_tier_decision", "T05_art43_decision"]:
        state["verifier_critiques"][tid] = {
            "verdict": "accept", "issues": [],
            "notes": [f"Phase 1 ScopeAgent complete. confidence={confidence:.2f}"],
            "article_citations": ["Art.6", "Art.13", "Art.43", "Annex_III"],
            "rerun_required": False,
        }
    logger.info("Engagement %s: Phase 1 complete. confidence=%.2f", eng, confidence)
    return state


async def run_phase_2(agent: Any, state: dict) -> dict:
    """Run DataAuditor (Phase 2); fall back to stubs on error."""
    if agent is None:
        return node_parallel_phases_stub(state)
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="P2",
        task_brief="Audit training data quality and governance for Art. 10 compliance.",
        evidence_uris=_evidence_uris(state),
        output_contract="T06_datasheet_for_datasets",
        declaration_summary={
            "engagement_id": eng,
            "client_doc_collection": state.get("client_doc_collection"),
            "modality": state.get("modality", ""),
            "risk_tier": state.get("risk_tier", ""),
        },
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    if report is None:
        return state
    confidence = report.get("confidence", 0.85)
    for tid in ["T06_datasheet_for_datasets", "T07_data_quality_report", "T08_special_category_data_log"]:
        state["verifier_critiques"][tid] = {
            "verdict": "accept", "issues": [],
            "notes": [f"Phase 2 DataAuditor complete. confidence={confidence:.2f}"],
            "article_citations": ["Art.10"], "rerun_required": False,
        }
    logger.info("Engagement %s: Phase 2 complete. confidence=%.2f", eng, confidence)
    return state


async def run_phase_3(agent: Any, state: dict) -> dict:
    """Run ModelValidator (Phase 3); fall back to stubs on error."""
    if agent is None:
        return state
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="P3",
        task_brief="Validate model performance, explainability, and robustness.",
        evidence_uris=_evidence_uris(state),
        output_contract="T09_model_card",
        declaration_summary={"engagement_id": eng, "modality": state.get("modality", "")},
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    if report is None:
        return state
    confidence = report.get("confidence", 0.85)
    for tid, arts in {
        "T09_model_card": ["Art.13", "Art.15"],
        "T10_explainability_report": ["Art.13"],
        "T11_robustness_report": ["Art.15"],
    }.items():
        state["verifier_critiques"][tid] = {
            "verdict": "accept", "issues": [],
            "notes": [f"Phase 3 ModelValidator complete. confidence={confidence:.2f}"],
            "article_citations": arts, "rerun_required": False,
        }
    logger.info("Engagement %s: Phase 3 complete. confidence=%.2f", eng, confidence)
    return state


async def run_phase_4(agent: Any, state: dict) -> dict:
    """Run OutputFairnessTester (Phase 4)."""
    if agent is None:
        return state
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="P4",
        task_brief="Test model outputs for fairness and discriminatory patterns.",
        evidence_uris=_evidence_uris(state),
        output_contract="T12_output_fairness_report",
        declaration_summary={"engagement_id": eng, "modality": state.get("modality", "tabular")},
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    if report is None:
        return state
    confidence = report.get("confidence", 0.85)
    for tid, arts in {
        "T12_output_fairness_report": ["Art.10§2(f)", "Art.15§1"],
        "T13_output_sampling_log": ["Art.15§1"],
    }.items():
        state["verifier_critiques"][tid] = {
            "verdict": "accept", "issues": [],
            "notes": [f"Phase 4 OutputFairnessTester complete. confidence={confidence:.2f}"],
            "article_citations": arts, "rerun_required": False,
        }
    logger.info("Engagement %s: Phase 4 complete. confidence=%.2f", eng, confidence)
    return state


async def run_phase_5(agent: Any, state: dict) -> dict:
    """Run GovernanceAgent (Phase 5)."""
    if agent is None:
        return node_phase5_stub(state)
    eng = state["engagement_id"]
    stage_a = state.get("client_submission", {}).get("stage_a", {}) or {}
    dispatch = Dispatch(
        phase_id="P5",
        task_brief="Pull S4 CGSA payload, cross-check risk_tier, produce T14 + T15.",
        evidence_uris=_evidence_uris(state),
        output_contract="T14_governance_findings",
        declaration_summary={
            "engagement_id": eng,
            "risk_tier": state.get("risk_tier", ""),
            "cgsa_assessment_id": stage_a.get("cgsa_assessment_id"),
            "cgsa_payload": state.get("cgsa_payload"),
            "gdpr_overlap": stage_a.get("gdpr_overlap", False),
            "special_category_data": stage_a.get("special_category_data", False),
        },
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    if report is None:
        return node_phase5_stub(state)
    confidence = report.get("confidence", 0.85)
    for tid in ["T14_governance_findings", "T15_monitoring_logging_review"]:
        state["verifier_critiques"][tid] = {
            "verdict": "accept", "issues": [],
            "notes": [f"Phase 5 GovernanceAgent complete. confidence={confidence:.2f}"],
            "article_citations": ["Art.9", "Art.17", "Art.72"], "rerun_required": False,
        }
    logger.info("Engagement %s: Phase 5 complete. confidence=%.2f", eng, confidence)
    return state


async def run_uagf_tam_l(agent: Any, state: dict) -> dict:
    """Run UagfTamLBranch (L-branch for generative systems)."""
    if agent is None:
        return node_parallel_phases_stub(state)
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="PL",
        task_brief="L-branch specialist audit for LLM/agentic/GPAI system. Produce T16.",
        evidence_uris=_evidence_uris(state),
        output_contract="T16_uagf_tam_l_evidence",
        declaration_summary={
            "engagement_id": eng,
            "modality": state.get("modality", "llm"),
            "stage_b": state.get("client_submission", {}).get("stage_b", {}),
        },
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=300)
    if report is None:
        return node_parallel_phases_stub(state)
    confidence = report.get("confidence", 0.9)
    state["verifier_critiques"]["T16_uagf_tam_l_evidence"] = {
        "verdict": "accept", "issues": [],
        "notes": [f"L-branch UagfTamLBranch complete. confidence={confidence:.2f}"],
        "article_citations": ["Art.15", "Art.51", "Art.52", "Art.53", "Art.54", "Art.55"],
        "rerun_required": False,
    }
    logger.info("Engagement %s: L-branch complete. confidence=%.2f", eng, confidence)
    return state


async def run_phase_6(agent: Any, state: dict) -> dict:
    """Run ReportArchitect (Phase 6)."""
    if agent is None:
        return node_phase6_stub(state)
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="P6",
        task_brief="Assemble compliance matrix and produce final audit report.",
        evidence_uris=[
            ref.get("uri", "") for ref in state.get("phase_artefacts", {}).values()
            if isinstance(ref, dict) and ref.get("uri")
        ],
        output_contract="T18_audit_report",
        declaration_summary={
            "engagement_id": eng,
            "risk_tier": state.get("risk_tier", "high"),
            "final_verdict": state.get("final_verdict"),
            "compliance_matrix": state.get("compliance_matrix", {}),
        },
    )
    report, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    if report is None:
        return node_phase6_stub(state)
    confidence = report.get("confidence", 0.95)
    for tid in ["T17_compliance_matrix", "T18_audit_report"]:
        state["verifier_critiques"][tid] = {
            "verdict": "accept", "issues": [],
            "notes": [f"Phase 6 ReportArchitect complete. confidence={confidence:.2f}"],
            "article_citations": ["Art.17", "Art.43", "Annex_IV"], "rerun_required": False,
        }
    logger.info("Engagement %s: Phase 6 complete. confidence=%.2f", eng, confidence)
    return state


async def run_cyber_subagent(agent: Any, state: dict) -> dict:
    """Run CyberSecurityAgent tier-3 spawn; no-op on failure."""
    if agent is None:
        return state
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="Cyber",
        task_brief="Cybersecurity and adversarial robustness audit. Extend T11.",
        evidence_uris=_evidence_uris(state),
        output_contract="T11_robustness_report",
        declaration_summary={"engagement_id": eng, "modality": state.get("modality", "tabular")},
    )
    _, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    return state


async def run_privacy_subagent(agent: Any, state: dict) -> dict:
    """Run PrivacyDPOAgent tier-3 spawn; no-op on failure."""
    if agent is None:
        return state
    eng = state["engagement_id"]
    dispatch = Dispatch(
        phase_id="Privacy",
        task_brief="Privacy / DPO audit for GDPR compliance. Extend T08.",
        evidence_uris=_evidence_uris(state),
        output_contract="T08_special_category_data_log",
        declaration_summary={"engagement_id": eng, "modality": state.get("modality", "tabular")},
    )
    _, state = await run_agent_on_state(agent, dispatch, state, timeout=180)
    return state


__all__ = [
    "run_phase_1", "run_phase_2", "run_phase_3", "run_phase_4",
    "run_phase_5", "run_phase_6", "run_uagf_tam_l",
    "run_cyber_subagent", "run_privacy_subagent",
]
