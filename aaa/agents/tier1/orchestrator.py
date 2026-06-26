"""
Orchestrator — Tier-1 lead agent (§3.1 #1, §6).

Thin coordinator that wires the 9-node LangGraph StateGraph.
All node implementations live in ``aaa.agents.tier1.phases.*``.

  stage_0 → plan → phase_1 → route → parallel_phases
          → phase_5 → compliance_matrix → hitl_checkpoint → phase_6
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from aaa.agents.base import BaseAgent
from aaa.agents.tier1.verifier import Verifier
from aaa.agents.tier1.checkpointer import make_checkpointer, make_async_checkpointer
from aaa.agents.tier1.agent_initializer import initialise_agents
from aaa.agents.tier1.phases.initial_state import build_initial_state
from aaa.agents.tier1.phases.node_stage0 import node_stage0
from aaa.agents.tier1.phases.node_plan import node_plan
from aaa.agents.tier1.phases.node_stubs import (
    node_route,
    node_hitl_checkpoint,
    should_hitl,
)
from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
from aaa.agents.tier1.phases.phase_runners import (
    run_phase_1, run_phase_2, run_phase_3, run_phase_4,
    run_phase_5, run_phase_6, run_uagf_tam_l,
    run_cyber_subagent, run_privacy_subagent,
)
from aaa.platform.model_registry import resolve_model, resolve_service_tier

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Orchestrator class
# ---------------------------------------------------------------------------

# (All helper functions now live in aaa.agents.tier1.phases.*)

def _unused_initial_state_kept_for_compat(engagement_id: str, client_submission: dict) -> dict:  # noqa: N802
    """Seed a minimal AuditState for a new engagement."""
    stage_a = client_submission.get("stage_a", {})
    return {
        "engagement_id": engagement_id,
        "client_doc_collection": client_submission.get("client_doc_collection"),
        "client_submission": client_submission,
        "declared_modality": stage_a.get("declared_modality", "tabular"),
        "declared_risk_tier": stage_a.get("declared_risk_tier", "minimal"),
        "declared_annex_iii_sections": stage_a.get("declared_annex_iii_sections", []),
        "risk_tier": stage_a.get("declared_risk_tier", "minimal"),
        "modality": stage_a.get("declared_modality", "tabular"),
        "deployment_context": stage_a.get("deployment_context", "b2b"),
        "is_llm_or_agentic": stage_a.get("declared_modality", "") in {
            "llm", "agentic", "gpai"
        },
        "provider_elects_third_party": stage_a.get("provider_elects_third_party", False),
        "harmonised_standards_applied": False,
        "annex_iii_mapping": [],
        "declaration_verification": {},
        "art43_decision": None,
        "phase_status": {},
        "phase_artefacts": {},
        "cgsa_payload": None,
        "cgsa_schema_version": None,
        "cgsa_composite_maturity_score": None,
        "cgsa_composite_maturity_label": None,
        "cgsa_domain_scores": None,
        "cgsa_eu_ai_act_coverage_pct": None,
        "cgsa_csp_satisfiable": None,
        "cgsa_governance_verdict": None,
        "cgsa_phase5_verdict": None,
        "cgsa_phase5_narrative": None,
        "cgsa_blocking_findings": [],
        "cgsa_positive_findings": [],
        "cgsa_low_confidence_controls": [],
        "cgsa_recommended_follow_up": [],
        "cgsa_report_url": None,
        "cgsa_risk_tier_match": None,
        "compliance_matrix": {},
        "blocking_findings": [],
        "positive_findings": [],
        "remediation_roadmap": [],
        "material_findings_count": None,
        "possibly_material_findings_count": None,
        "verifier_critiques": {},
        "intake_completeness_score": client_submission.get("intake_completeness_score"),
        "completeness_score": None,
        "regulatory_coverage_pct": None,
        "final_verdict": None,
        "auditor_opinion": None,
        "hitl_required": False,
        "hitl_reason": None,
    }


# ---------------------------------------------------------------------------
# Graph node functions
# ---------------------------------------------------------------------------

def _node_stage_0(state: dict) -> dict:
    """
    Stage 0 — Intake validation gate.

    Checks that intake_completeness_score ≥ 0.80 before advancing.
    (IntakeValidator already ran before the Orchestrator; this node simply
    enforces the gate and surfaces the score on AuditState.)
    """
    score = state.get("intake_completeness_score") or 0.0
    if score < 0.80:
        state["hitl_required"] = True
        state["hitl_reason"] = (
            f"intake_completeness_score={score:.2f} is below the 0.80 gate. "
            "Client must remediate missing Annex IV fields before Phase 1 can run."
        )
        logger.warning("Engagement %s blocked at Stage 0: score=%.2f", state["engagement_id"], score)
    return state


# Mapping from CSP phase variables → template IDs produced by each phase.
# Used to expand the phase-level CSP output to template-level phase_status.
_PHASE_TO_TEMPLATES: dict[str, list[str]] = {
    "P1":   ["T02_system_card", "T03_annex_iii_mapping",
             "T04_risk_tier_decision", "T05_art43_decision"],
    "P2":   ["T06_datasheet_for_datasets", "T07_data_quality_report",
             "T08_special_category_data_log"],
    "P3":   ["T09_model_card", "T10_explainability_report", "T11_robustness_report"],
    "P4":   ["T12_output_fairness_report", "T13_output_sampling_log"],
    "P5":   ["T14_governance_findings", "T15_monitoring_logging_review"],
    "P6":   ["T17_compliance_matrix", "T18_audit_report"],
    "L":    ["T16_uagf_tam_l_evidence"],
    "CYBER": [],   # Cyber findings extend T11/T14; no standalone template
    "PRIV":  [],   # Privacy findings extend T08/T14; no standalone template
}


def _node_plan(state: dict) -> dict:
    """
    Plan — Run CSP solver to produce phase_status (M/O/S per template).

    Uses declared values for the preview plan (final plan is recomputed
    after Phase 1 against verified values).

    The CSP operates at phase-variable level (P1-P6, L, CYBER, PRIV).
    We expand the result to template-ID level so completeness_score and
    regulatory_coverage work directly on phase_artefacts keys.
    """
    try:
        phase_plan = solve_phase_plan(state)
        # Expand to template-level: phase_status is keyed by template ID
        template_status: dict[str, str] = {}
        for phase_var, status in phase_plan.items():
            for tid in _PHASE_TO_TEMPLATES.get(phase_var, []):
                template_status[tid] = status
        state["phase_status"] = template_status
        logger.info("Engagement %s phase plan: %s", state["engagement_id"], phase_plan)
        logger.debug("Template-level phase_status: %s", template_status)
    except ValueError as exc:
        state["hitl_required"] = True
        state["hitl_reason"] = f"CSP over-constrained: {exc}"
        logger.error("CSP failed for engagement %s: %s", state["engagement_id"], exc)
    return state


def _node_phase_1(state: dict) -> dict:
    """
    Phase 1 — Scope and Risk Classifier (Declaration Verifier).

    Stub: in production, dispatches ScopeAgent (Group 4).
    Records a placeholder verifier critique so downstream nodes can proceed.
    """
    logger.info("Engagement %s: Phase 1 (Scope) — stub", state["engagement_id"])
    # Stub artefact reference for T02–T05
    for tid in ["T02_system_card", "T03_annex_iii_mapping",
                "T04_risk_tier_decision", "T05_art43_decision"]:
        state["phase_artefacts"][tid] = {
            "uri": f"mem://{state['engagement_id']}/{tid}",
            "sha256": "stub",
            "template_id": tid,
        }
        state["verifier_critiques"][tid] = {
            "verdict": "accept",
            "issues": [],
            "notes": ["Phase 1 stub — real ScopeAgent wired in Group 4."],
            "article_citations": [],
            "rerun_required": False,
        }
    return state


def _node_route(state: dict) -> dict:
    """
    Route — Determines which branch (standard / L-branch) to follow.

    Sets state["_branch"] = "l_branch" | "standard".
    """
    state["_branch"] = "l_branch" if state.get("is_llm_or_agentic") else "standard"
    logger.info("Engagement %s routed to %s branch", state["engagement_id"], state["_branch"])
    return state


def _node_parallel_phases(state: dict) -> dict:
    """
    Parallel Phases (2/3/4 or L-branch).

    Standard: stubs for Data Auditor, Model Validator, Output Fairness.
    L-branch: stub for UAGF-TAM-L specialist.
    All wired in Groups 5–7 and 10.
    """
    branch = state.get("_branch", "standard")
    if branch == "l_branch":
        tids = ["T16_uagf_tam_l_evidence"]
    else:
        tids = [
            "T06_datasheet_for_datasets", "T07_data_quality_report",
            "T08_special_category_data_log", "T09_model_card",
            "T10_explainability_report", "T11_robustness_report",
            "T12_output_fairness_report", "T13_output_sampling_log",
        ]
    for tid in tids:
        if tid not in state["phase_artefacts"]:
            state["phase_artefacts"][tid] = {
                "uri": f"mem://{state['engagement_id']}/{tid}",
                "sha256": "stub",
                "template_id": tid,
            }
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"{tid} stub — real agent wired in Groups 5–7/10."],
                "article_citations": [],
                "rerun_required": False,
            }
    return state


def _node_phase_5(state: dict) -> dict:
    """
    Phase 5 — Governance (S4 CGSA integration).

    Stub: real GovernanceAgent wired in Group 8.
    """
    logger.info("Engagement %s: Phase 5 (Governance) — stub", state["engagement_id"])
    for tid in ["T14_governance_findings", "T15_monitoring_logging_review"]:
        state["phase_artefacts"][tid] = {
            "uri": f"mem://{state['engagement_id']}/{tid}",
            "sha256": "stub",
            "template_id": tid,
        }
        state["verifier_critiques"][tid] = {
            "verdict": "accept",
            "issues": [],
            "notes": ["Phase 5 stub — real GovernanceAgent wired in Group 8."],
            "article_citations": [],
            "rerun_required": False,
        }
    return state


# NOTE: compliance-matrix assembly + final verdict now lives solely in
# ``aaa.agents.tier1.phases.compliance_matrix.node_compliance_matrix`` (imported
# above, wired into both the LangGraph and sequential paths). The previous local
# duplicate that auto-stamped every admitted article ``PASS`` has been removed so it
# can never be re-wired by accident.


def _node_hitl_checkpoint(state: dict) -> dict:
    """
    HITL Checkpoint (§6 step 7, §8.4).

    In production this pauses the graph and notifies a human reviewer.
    In offline/demo mode it auto-approves with a warning log.
    """
    needs_hitl = state.get("hitl_required") or state.get("final_verdict") == "FAIL"
    if needs_hitl:
        reason = state.get("hitl_reason") or "FAIL verdict or manual escalation"
        if _OFFLINE:
            logger.warning("HITL required (%s) — auto-approved in offline mode.", reason)
        else:
            logger.warning("HITL required (%s) — pausing for human review.", reason)
            # In production: send notification, wait for approval signal.
    return state


def _node_phase_6(state: dict) -> dict:
    """
    Phase 6 — Report Architect.

    Stub: real ReportArchitect wired in Group 9.
    """
    logger.info("Engagement %s: Phase 6 (Report) — stub", state["engagement_id"])
    state["phase_artefacts"]["T17_compliance_matrix"] = {
        "uri": f"mem://{state['engagement_id']}/T17_compliance_matrix",
        "sha256": "stub",
        "template_id": "T17_compliance_matrix",
    }
    state["phase_artefacts"]["T18_audit_report"] = {
        "uri": f"mem://{state['engagement_id']}/T18_audit_report",
        "sha256": "stub",
        "template_id": "T18_audit_report",
    }
    return state


# ---------------------------------------------------------------------------
# Router edge function
# ---------------------------------------------------------------------------

def _should_hitl(state: dict) -> str:
    """Edge: advance to phase_6 or stop at hitl_checkpoint."""
    if state.get("hitl_required") and not _OFFLINE:
        return "wait_hitl"
    return "phase_6"


# ---------------------------------------------------------------------------
# Orchestrator class
# ---------------------------------------------------------------------------

class Orchestrator(BaseAgent):
    """Lead orchestrator — thin coordinator that delegates to phase modules.

    Parameters
    ----------
    model : optional LLM model override.
    evidence_store : optional EvidenceStore; enables real phase agents.
    regulatory_rag : optional RegulatoryRAG passed to ScopeAgent.
    service_tier : optional OpenAI service tier override.
    """

    def __init__(
        self,
        model: str | None = None,
        evidence_store: Any = None,
        regulatory_rag: Any = None,
        service_tier: str | None = None,
    ):
        super().__init__(
            name="Orchestrator",
            model=resolve_model("Orchestrator", model),
            service_tier=resolve_service_tier("Orchestrator", service_tier),
        )
        self._verifier = Verifier()
        self._checkpointer = make_checkpointer()
        self._evidence_store = evidence_store
        # All phase agents loaded via initialise_agents (fails gracefully per agent)
        self._agents: dict[str, Any] = initialise_agents(
            evidence_store=evidence_store,
            regulatory_rag=regulatory_rag,
        )
        self._graph = self._build_graph()

    # NOTE: All phase node implementations have been moved to
    # aaa.agents.tier1.phases.phase_runners.  The _build_graph method below
    # uses async wrappers bound to self._agents.

    def _node_phase_1_impl(self, state: dict) -> dict:  # sync LangGraph wrapper
        """Sync wrapper — delegates to async run_phase_1 via thread pool."""
        import asyncio, concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, run_phase_1(self._agents.get("scope_agent"), state)
            ).result(timeout=120)

    def _node_parallel_phases_impl(self, state: dict) -> dict:
        """Sync LangGraph wrapper for Phases 2–4 / L-branch."""
        import asyncio, concurrent.futures

        async def _run(s: dict) -> dict:
            if s.get("_branch") == "l_branch":
                return await run_uagf_tam_l(self._agents.get("uagf_tam_l"), s)
            s = await run_phase_2(self._agents.get("data_auditor"), s)
            s = await run_phase_3(self._agents.get("model_validator"), s)
            return await run_phase_4(self._agents.get("output_fairness"), s)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _run(state)).result(timeout=300)

    def _node_phase_5_impl(self, state: dict) -> dict:
        """Sync LangGraph wrapper for Phase 5 (GovernanceAgent)."""
        import asyncio, concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, run_phase_5(self._agents.get("governance_agent"), state)
            ).result(timeout=180)

    def _node_phase_6_impl(self, state: dict) -> dict:
        """Sync LangGraph wrapper for Phase 6 (ReportArchitect)."""
        import asyncio, concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, run_phase_6(self._agents.get("report_architect"), state)
            ).result(timeout=180)

    def _build_graph(self, checkpointer: Any | None = None) -> Any:
        """Build and compile the LangGraph StateGraph (or return None if unavailable)."""
        try:
            from langgraph.graph import StateGraph, END  # type: ignore

            g = StateGraph(dict)
            g.add_node("stage_0", node_stage0)
            g.add_node("plan", node_plan)
            g.add_node("phase_1", self._node_phase_1_impl)
            g.add_node("route", node_route)
            g.add_node("parallel_phases", self._node_parallel_phases_impl)
            g.add_node("phase_5", self._node_phase_5_impl)
            g.add_node("compliance_matrix", node_compliance_matrix)
            g.add_node("hitl_checkpoint", lambda s: node_hitl_checkpoint(s))
            g.add_node("phase_6", self._node_phase_6_impl)

            g.set_entry_point("stage_0")
            g.add_edge("stage_0", "plan")
            g.add_edge("plan", "phase_1")
            g.add_edge("phase_1", "route")
            g.add_edge("route", "parallel_phases")
            g.add_edge("parallel_phases", "phase_5")
            g.add_edge("phase_5", "compliance_matrix")
            g.add_edge("compliance_matrix", "hitl_checkpoint")
            g.add_conditional_edges(
                "hitl_checkpoint",
                should_hitl,
                {"phase_6": "phase_6", "wait_hitl": END},
            )
            g.add_edge("phase_6", END)
            return g.compile(checkpointer=checkpointer)
        except ImportError:
            logger.info("LangGraph not installed; using sequential offline runner.")
            return None

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: dict) -> dict:  # type: ignore[override]
        """
        Run a full engagement audit.

        Parameters
        ----------
        message : dict with keys:
            engagement_id     – str (UUID)
            client_submission – dict (ClientSubmission)

        Returns
        -------
        Final AuditState dict.
        """
        engagement_id = message.get("engagement_id") or str(uuid.uuid4())
        client_submission = message.get("client_submission", {})
        state = build_initial_state(engagement_id, client_submission)
        return await self.run(state)

    async def run(self, state: dict) -> dict:
        """Execute the graph (or sequential fallback) and return final state."""
        if not _OFFLINE:
            try:
                async with make_async_checkpointer() as checkpointer:
                    await checkpointer.setup()
                    graph = self._build_graph(checkpointer=checkpointer)
                    if graph is not None:
                        return await self._run_langgraph(state, graph)
            except Exception as exc:
                logger.warning(
                    "AsyncPostgresSaver unavailable (%s); falling back to uncheckpointed graph.",
                    exc,
                )
        if self._graph is not None:
            return await self._run_langgraph(state)
        return self._run_sequential(state)

    async def _run_langgraph(self, state: dict, graph: Any | None = None) -> dict:  # pragma: no cover
        """Invoke the compiled LangGraph; return final state."""
        config = {"configurable": {"thread_id": state["engagement_id"]}}
        final: dict = {}
        graph = graph or self._graph
        if graph is None:
            return self._run_sequential(state)
        async for chunk in graph.astream(state, config=config):
            final = chunk
        if len(final) == 1:
            maybe_state = next(iter(final.values()))
            if isinstance(maybe_state, dict) and "engagement_id" in maybe_state:
                return maybe_state
        return final

    def _run_sequential(self, state: dict) -> dict:
        """Sequential fallback: run all nodes in order (offline/CI)."""
        import asyncio

        async def _pipeline(s: dict) -> dict:
            s = node_stage0(s)
            s = node_plan(s)
            s = await run_phase_1(self._agents.get("scope_agent"), s)
            s = node_route(s)
            if s.get("_branch") == "l_branch":
                s = await run_uagf_tam_l(self._agents.get("uagf_tam_l"), s)
            else:
                s = await run_phase_2(self._agents.get("data_auditor"), s)
                s = await run_phase_3(self._agents.get("model_validator"), s)
                s = await run_phase_4(self._agents.get("output_fairness"), s)
            s = await run_phase_5(self._agents.get("governance_agent"), s)
            if self._agents.get("cyber_agent"):
                s = await run_cyber_subagent(self._agents["cyber_agent"], s)
            if self._agents.get("privacy_agent"):
                s = await run_privacy_subagent(self._agents["privacy_agent"], s)
            s = node_compliance_matrix(s)
            s = node_hitl_checkpoint(s)
            if not (s.get("hitl_required") and not _OFFLINE):
                s = await run_phase_6(self._agents.get("report_architect"), s)
            return s

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, _pipeline(state)).result(timeout=600)
            return loop.run_until_complete(_pipeline(state))
        except RuntimeError:
            return asyncio.run(_pipeline(state))

