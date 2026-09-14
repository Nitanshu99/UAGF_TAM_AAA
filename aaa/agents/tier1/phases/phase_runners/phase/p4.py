"""Part 5 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p3 import run_phase_3  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification
from aaa.tools.csp_solver.catalogue import discriminative_modality


async def run_phase_4(agent: Any, state: dict) -> dict:
    """Run OutputFairnessTester (Phase 4)."""
    if agent is None:
        return state
    eng = state["engagement_id"]
    stage_b = state.get("client_submission", {}).get("stage_b", {}) or {}
    dispatch = Dispatch(
        phase_id="P4",
        task_brief="Test model outputs for fairness and discriminatory patterns.",
        evidence_uris=_evidence_uris(state),
        output_contract="T12_output_fairness_report",
        declaration_summary={
            "engagement_id": eng,
            # The discriminative component's modality, not the system's (F3).
            "modality": discriminative_modality(state) or "tabular",
            "client_doc_collection": state.get("client_doc_collection"),
            # The verified tier, so artefacts say when an article does not bind (T-092).
            "risk_tier": state.get("risk_tier", ""),
            "stage_b": stage_b,
        },
    )
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            # Fix 47 (R15): Art. 15 §1 is accuracy, robustness and cybersecurity.
            # The obligation these two artefacts discharge is the Art. 10 §2(f)
            # examination for possible biases. Art. 9 is named by the *findings*
            # (see `output_fairness.verdicts.FINDING_ARTICLES`) but not here:
            # a contract lists what the phase must evidence, and Phase 5 — not
            # Phase 4 — assesses the risk-management system.
            "T12_output_fairness_report": ["Art.10§2(f)"],
            "T13_output_sampling_log": ["Art.10§2(f)"],
        },
        phase_label="Phase 4 OutputFairnessTester", default_confidence=0.85,
    )
    if report is None:
        return state
    logger.info("Engagement %s: Phase 4 complete.", eng)
    return state
