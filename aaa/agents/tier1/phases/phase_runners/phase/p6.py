"""Part 9 of the former ``phase_runners`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.node_stubs import node_phase6_stub
from aaa.agents.tier1.phases.phase_runners.client_brief_step import run_client_brief
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p2 import run_phase_2  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p3 import run_phase_3  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p4 import run_phase_4  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p5 import run_phase_5  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase6_declaration_summary import (  # noqa: F401
    _phase6_declaration_summary,
)
from aaa.agents.tier1.phases.phase_runners.uagf_tam_l import run_uagf_tam_l  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification


async def run_phase_6(agent: Any, state: dict, brief_agent: Any = None) -> dict:
    """Run ReportArchitect (Phase 6), then write the customer's brief.

    :param agent: The ``ReportArchitect``, or ``None`` when unwired.
    :param state: Current ``AuditState``.
    :param brief_agent: The ``ClientBriefAgent``. ``None`` skips the brief —
        the audit is complete without it, and it must never gate the report.
    """
    if agent is None:
        return node_phase6_stub(state)
    eng = state["engagement_id"]
    stage_a = state.get("client_submission", {}).get("stage_a", {}) or {}
    dispatch = Dispatch(
        phase_id="P6",
        task_brief="Assemble compliance matrix and produce final audit report.",
        evidence_uris=[
            ref.get("uri", "") for ref in state.get("phase_artefacts", {}).values()
            if isinstance(ref, dict) and ref.get("uri")
        ],
        output_contract="T18_audit_report",
        declaration_summary=_phase6_declaration_summary(state, eng, stage_a),
    )
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            "T17_compliance_matrix": ["Art.17"],
            "T18_audit_report": ["Art.43", "Annex_IV"],
        },
        phase_label="Phase 6 ReportArchitect", default_confidence=0.95,
    )
    if report is None:
    # Fix 35: the *unwired* path above still stubs — no dispatch was attempted
    # and a deterministic placeholder is an honest answer there. A phase that
    # was dispatched and failed is a different fact, and `gate_on_no_report`
    # has already recorded it: no artefact, articles held, a finding naming
    # the cause. Writing a stub here instead is what produced R2 and R3.
        return state
    logger.info("Engagement %s: Phase 6 complete.", eng)
    return await run_client_brief(brief_agent, state)
