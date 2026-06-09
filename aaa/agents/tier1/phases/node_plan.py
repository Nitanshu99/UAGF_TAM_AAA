"""
aaa.agents.tier1.phases.node_plan — CSP planning node.

Single exported function: ``node_plan(state)``.

Runs the CSP solver to produce a phase_status mapping (M/O/S per template).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Mapping from CSP phase variables → template IDs produced by each phase.
PHASE_TO_TEMPLATES: dict[str, list[str]] = {
    "P1":    ["T02_system_card", "T03_annex_iii_mapping",
              "T04_risk_tier_decision", "T05_art43_decision"],
    "P2":    ["T06_datasheet_for_datasets", "T07_data_quality_report",
              "T08_special_category_data_log"],
    "P3":    ["T09_model_card", "T10_explainability_report", "T11_robustness_report"],
    "P4":    ["T12_output_fairness_report", "T13_output_sampling_log"],
    "P5":    ["T14_governance_findings", "T15_monitoring_logging_review"],
    "P6":    ["T17_compliance_matrix", "T18_audit_report"],
    "L":     ["T16_uagf_tam_l_evidence"],
    "CYBER": [],
    "PRIV":  [],
}


def node_plan(state: dict) -> dict:
    """Plan — run CSP solver and expand results to template-level phase_status."""
    from aaa.tools.csp_solver import solve_phase_plan

    try:
        phase_plan = solve_phase_plan(state)
        template_status: dict[str, str] = {}
        for phase_var, status in phase_plan.items():
            for tid in PHASE_TO_TEMPLATES.get(phase_var, []):
                template_status[tid] = status
        state["phase_status"] = template_status
        logger.info("Engagement %s phase plan: %s", state["engagement_id"], phase_plan)
        logger.debug("Template-level phase_status: %s", template_status)
    except ValueError as exc:
        state["hitl_required"] = True
        state["hitl_reason"] = f"CSP over-constrained: {exc}"
        logger.error("CSP failed for engagement %s: %s", state["engagement_id"], exc)
    return state


__all__ = ["node_plan", "PHASE_TO_TEMPLATES"]
