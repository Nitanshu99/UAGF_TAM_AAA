"""Part 2 of the former ``node_stubs`` module (auto-split)."""
from __future__ import annotations

from aaa.agents.tier1.phases.node_stubs.logger import (  # noqa: F401
    TEMPLATE_ARTICLES,
    _mark_stub_insufficient,
    _stub_artefact,
    _stub_critique,
    logger,
    node_phase1_stub,
)


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
