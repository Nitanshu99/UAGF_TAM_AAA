"""Part 7 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris
from aaa.agents.tier1.phases.node_stubs import node_parallel_phases_stub
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p3 import run_phase_3  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p4 import run_phase_4  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p5 import run_phase_5  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification


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
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            # Fix 49 (R17): `GPAI_5x` is the canonical spelling — what ARTICLE_SET,
            # the scope gate, ARTICLE_PHASE and the regulatory corpus all use.
            "T16_uagf_tam_l_evidence": [
                "Art.15", "GPAI_51", "GPAI_52", "GPAI_53", "GPAI_54", "GPAI_55",
            ],
        },
        phase_label="L-branch UagfTamLBranch", default_confidence=0.9,
    )
    if report is None:
    # Fix 35: the *unwired* path above still stubs — no dispatch was attempted
    # and a deterministic placeholder is an honest answer there. A phase that
    # was dispatched and failed is a different fact, and `gate_on_no_report`
    # has already recorded it: no artefact, articles held, a finding naming
    # the cause. Writing a stub here instead is what produced R2 and R3.
        return state
    logger.info("Engagement %s: L-branch complete.", eng)
    return state
