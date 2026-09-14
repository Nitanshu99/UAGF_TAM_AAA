"""
aaa.agents.tier1.phases.nodes.plan — CSP planning node.

Single exported function: ``node_plan(state)``.

Runs the CSP solver to produce a phase_status mapping (M/O/S per template), then
makes an optional phase mandatory when the evidence it examines was supplied.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from aaa.platform.state import AuditState

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


def _skip_rationale(state: dict, plan: dict) -> dict[str, str]:
    """Say why each skipped phase was skipped, in the plan itself.

    The plan is solved once, from the declaration, before any phase dispatches.
    A phase pinned ``S`` therefore leaves no artefact and no stub, and the only
    trace it was ever considered is this line.

    :param state: The AuditState the plan was solved from.
    :param plan: Phase variable → status.
    :returns: Phase variable → the reason it is not mandatory.
    """
    from aaa.tools.csp_solver.catalogue import DISCRIMINATIVE, component_modalities

    modalities = component_modalities(state)
    discriminative = sorted(set(modalities) & DISCRIMINATIVE)
    why = (f"components declared: {', '.join(modalities) or 'none'}"
           + ("" if discriminative else
              "; none of them ranks, scores or classifies, so the phases that "
              "examine a discriminative model were not scheduled"))
    return {phase: why for phase, status in plan.items() if status == "S"}


def node_plan(state: dict) -> dict:
    """Plan — run CSP solver and expand results to template-level phase_status."""
    from aaa.tools.csp_solver import solve_phase_plan
    from aaa.tools.csp_solver.supplied import promote_supplied

    try:
        # Graph nodes receive a plain dict carrying the AuditState keys.
        phase_plan = solve_phase_plan(cast("AuditState", state))
        promoted = promote_supplied(state, phase_plan)
        template_status: dict[str, str] = {}
        for phase_var, status in phase_plan.items():
            for tid in PHASE_TO_TEMPLATES.get(phase_var, []):
                template_status[tid] = status
        # Both the phase-variable plan and its template-level expansion are
        # persisted. The ReAct envelope (react/summary.py) and the coverage
        # guard (react/coverage.py) read ``phase_plan``; without it the
        # Orchestrator is told the plan is null on every turn, correctly keeps
        # answering PLAN, and exhausts its turn budget without dispatching —
        # while the guard that should force a dispatch sees an empty plan and
        # never fires either.
        state["phase_plan"] = phase_plan
        state["phase_status"] = template_status
        state["phase_plan_rationale"] = {**_skip_rationale(state, phase_plan), **promoted}
        logger.info("Engagement %s phase plan: %s", state["engagement_id"], phase_plan)
        logger.debug("Template-level phase_status: %s", template_status)
    except ValueError as exc:
        state["hitl_required"] = True
        state["hitl_reason"] = f"CSP over-constrained: {exc}"
        logger.error("CSP failed for engagement %s: %s", state["engagement_id"], exc)
    return state


__all__ = ["node_plan", "PHASE_TO_TEMPLATES"]
