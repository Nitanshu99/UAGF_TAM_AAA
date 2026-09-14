"""Part 4 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification
from aaa.tools.csp_solver.catalogue import discriminative_modality


async def run_phase_3(agent: Any, state: dict) -> dict:
    """Run ModelValidator (Phase 3); fall back to stubs on error."""
    if agent is None:
        return state
    eng = state["engagement_id"]
    stage_b = state.get("client_submission", {}).get("stage_b", {}) or {}
    dispatch = Dispatch(
        phase_id="P3",
        task_brief="Validate model performance, explainability, and robustness.",
        evidence_uris=_evidence_uris(state),
        output_contract="T09_model_card",
        declaration_summary={
            "engagement_id": eng,
            # The discriminative component's modality, not the system's (F3).
            "modality": discriminative_modality(state) or "",
            "client_doc_collection": state.get("client_doc_collection"),
            # The verified tier, so artefacts say when an article does not bind (T-092).
            "risk_tier": state.get("risk_tier", ""),
            # Real artefacts for independent re-computation (loaded by the agent).
            "stage_b": stage_b,
            "model_artifact_uri": stage_b.get("model_artifact_uri"),
            "evaluation_dataset_uri": stage_b.get("evaluation_dataset_uri"),
            "training_dataset_uri": stage_b.get("training_dataset_uri"),
        },
    )
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            "T09_model_card": ["Art.13", "Art.15"],
            "T10_explainability_report": ["Art.13"],
            "T11_robustness_report": ["Art.15"],
        },
        phase_label="Phase 3 ModelValidator", default_confidence=0.85,
    )
    if report is None:
        return state
    logger.info("Engagement %s: Phase 3 complete.", eng)
    return state
