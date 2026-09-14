"""Phase 2 runner — DataAuditor under verification, or the parallel-phase stub."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Dispatch
from aaa.agents.tier1.phases.agent_runner import _evidence_uris
from aaa.agents.tier1.phases.node_stubs import node_parallel_phases_stub
from aaa.agents.tier1.phases.phase_runners.logger import logger  # noqa: F401
from aaa.agents.tier1.phases.phase_runners.phase.p1 import run_phase_1  # noqa: F401
from aaa.agents.tier1.phases.verification import run_phase_with_verification
from aaa.tools.data_dictionary import explicit_data_dictionary


async def run_phase_2(agent: Any, state: dict) -> dict:
    """Run DataAuditor (Phase 2); fall back to stubs on error."""
    if agent is None:
        return node_parallel_phases_stub(state)
    eng = state["engagement_id"]
    stage_a = state.get("client_submission", {}).get("stage_a", {}) or {}
    stage_b = state.get("client_submission", {}).get("stage_b", {}) or {}
    block = explicit_data_dictionary(stage_b)
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
            "special_category_data": stage_a.get("special_category_data", False),
            "gdpr_overlap": stage_a.get("gdpr_overlap", False),
            # Resolved from the nested block *or* the top level: a CLI bundle
            # nests them and this dispatch used to read only the top level, so
            # the DataAuditor was told `target_column: None` for an engagement
            # whose dossier named it — and T06 then reported no sensitive
            # features for one that declares five.
            "target_column": block.get("target_column"),
            "positive_label": block.get("positive_label"),
            "sensitive_feature_columns": [str(c) for c in (block.get("sensitive_feature_columns") or [])],
            "stage_b": stage_b,
        },
    )
    report, state = await run_phase_with_verification(
        agent, dispatch, state,
        tid_articles={
            "T06_datasheet_for_datasets": ["Art.10"],
            "T07_data_quality_report": ["Art.10"],
            "T08_special_category_data_log": ["Art.10"],
        },
        phase_label="Phase 2 DataAuditor", default_confidence=0.85,
    )
    if report is None:
        return state
    logger.info("Engagement %s: Phase 2 complete.", eng)
    return state
