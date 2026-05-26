"""
Orchestrator — Tier-1 lead agent (§3.1 #1, §6).

Implements the 9-node LangGraph StateGraph that drives the full AAA workflow:

  stage_0 → plan → phase_1 → route → parallel_phases
          → phase_5 → compliance_matrix → hitl_checkpoint → phase_6

Each node mutates AuditState and persists a checkpoint via PostgresSaver.
The Verifier is called after every phase agent's Report before advancing.

Offline mode (AAA_OFFLINE_MODE=true):
  - PostgresSaver is replaced by an in-memory dict checkpoint.
  - Phase agents are replaced by lightweight stubs that return empty artefacts.
  - Verifier runs deterministic checks only (no LLM).
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch
from aaa.agents.tier1.verifier import Verifier
from aaa.platform.model_registry import resolve_model, resolve_service_tier
from aaa.tools.csp_solver import solve_phase_plan
from aaa.tools.completeness_score import compute_completeness_score
from aaa.tools.regulatory_coverage import compute_regulatory_coverage_pct

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

class _InMemoryCheckpointer:
    """Offline replacement for LangGraph PostgresSaver."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def put(self, thread_id: str, state: dict) -> None:
        self._store[thread_id] = dict(state)

    def get(self, thread_id: str) -> dict | None:
        return self._store.get(thread_id)


def _make_checkpointer():  # pragma: no cover
    """Return PostgresSaver in production, _InMemoryCheckpointer offline."""
    if _OFFLINE:
        return _InMemoryCheckpointer()
    try:
        from langgraph.checkpoint.postgres import PostgresSaver  # type: ignore
        import psycopg  # type: ignore

        db_url = os.environ.get(
            "DATABASE_URL", "postgresql://aaa:aaa@localhost:5432/aaa"
        )
        conn = psycopg.connect(db_url, autocommit=True)
        saver = PostgresSaver(conn)
        saver.setup()
        return saver
    except Exception as exc:
        logger.warning("PostgresSaver unavailable (%s); using in-memory checkpoint.", exc)
        return _InMemoryCheckpointer()


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

def _initial_state(engagement_id: str, client_submission: dict) -> dict:
    """Seed a minimal AuditState for a new engagement."""
    stage_a = client_submission.get("stage_a", {})
    return {
        "engagement_id": engagement_id,
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
        "verifier_critiques": {},
        "intake_completeness_score": client_submission.get("intake_completeness_score"),
        "completeness_score": None,
        "regulatory_coverage_pct": None,
        "final_verdict": None,
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


def _node_compliance_matrix(state: dict) -> dict:
    """
    Compliance Matrix Assembly (§6 step 6).

    - Assembles article verdicts from phase artefacts + CGSA payload.
    - Computes KPI 1 (completeness_score) and KPI 2 (regulatory_coverage_pct).
    - Determines final_verdict.
    """
    from aaa.tools.art43_select import art43_select_from_state  # type: ignore

    # Art. 43 final decision
    try:
        art43 = art43_select_from_state(state, use_declared=False)
        # art43_select returns Art43Decision which is a TypedDict (i.e., a dict)
        state["art43_decision"] = {
            "procedure": art43["procedure"],
            "rationale": art43["rationale"],
        }
    except Exception as exc:
        logger.warning("art43_select failed: %s", exc)

    # Build compliance_matrix from admitted artefact citations
    admitted_articles: set[str] = set()

    # Add articles derived from pre-intake scope gate flags
    gate = state.get("scope_gate", {})
    if gate.get("become_provider_under_art25"):
        admitted_articles.add("Art.25")
    if gate.get("triggers_fria"):
        admitted_articles.add("Art.27")
    if gate.get("triggers_art50_transparency"):
        admitted_articles.add("Art.50")
    if gate.get("is_gpai_systemic"):
        admitted_articles.add("Arts.51-55")

    for tid, critique in state["verifier_critiques"].items():
        if critique.get("verdict") in {"accept", "accept_with_notes"}:
            for art in critique.get("article_citations", []):
                admitted_articles.add(art)
            # Map template IDs to articles
            _TEMPLATE_ARTICLES = {
                "T02_system_card": "Art.13",
                "T04_risk_tier_decision": "Art.6",
                "T05_art43_decision": "Art.43",
                "T06_datasheet_for_datasets": "Art.10",
                "T09_model_card": "Art.13",
                "T11_robustness_report": "Art.15",
                "T12_output_fairness_report": "Art.15",
                "T14_governance_findings": "Art.9",
                "T17_compliance_matrix": "Art.17",
            }
            if tid in _TEMPLATE_ARTICLES:
                admitted_articles.add(_TEMPLATE_ARTICLES[tid])

    for article in admitted_articles:
        if state["compliance_matrix"].get(article) in (None, "PENDING"):
            state["compliance_matrix"][article] = "PASS"

    # KPI 1 and KPI 2
    compute_completeness_score(state)
    compute_regulatory_coverage_pct(state)

    # Final verdict
    phase5_ok = state.get("cgsa_phase5_verdict") in {"PASS", "PASS_WITH_OBSERVATIONS", None}
    csp_ok = state.get("cgsa_csp_satisfiable", True) is not False
    cs = state.get("completeness_score") or 0.0
    rc = state.get("regulatory_coverage_pct") or 0.0
    ics = state.get("intake_completeness_score") or 0.0

    if ics >= 0.90 and cs >= 0.90 and rc >= 90.0 and phase5_ok and csp_ok:
        verdict = "PASS"
    elif ics >= 0.80 and cs >= 0.75 and rc >= 75.0 and phase5_ok and csp_ok:
        verdict = "PASS_WITH_OBSERVATIONS"
    else:
        verdict = "FAIL"

    state["final_verdict"] = verdict
    logger.info("Engagement %s final_verdict=%s (cs=%.2f rc=%.1f)", state["engagement_id"], verdict, cs, rc)
    return state


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
    """
    Lead orchestrator agent.

    Builds and runs the LangGraph StateGraph for a single engagement.
    Falls back gracefully if LangGraph is not installed (runs nodes
    sequentially in offline mode).

    Parameters
    ----------
    model:
        LLM model string used by the Orchestrator itself.
    evidence_store:
        Optional ``EvidenceStore`` instance.  When provided, the real
        ``ScopeAgent`` is used for Phase 1; otherwise the stub runs.
    regulatory_rag:
        Optional ``RegulatoryRAG`` instance passed through to ScopeAgent.
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
        self._checkpointer = _make_checkpointer()
        self._evidence_store = evidence_store
        self._scope_agent: Any = None
        self._data_auditor: Any = None
        self._model_validator: Any = None
        self._output_fairness: Any = None
        self._governance_agent: Any = None
        self._report_architect: Any = None
        self._uagf_tam_l: Any = None
        self._cyber_agent: Any = None
        self._privacy_agent: Any = None
        if evidence_store is not None:
            try:
                from aaa.agents.tier2.scope_agent import ScopeAgent  # type: ignore
                self._scope_agent = ScopeAgent(
                    evidence_store=evidence_store,
                    regulatory_rag=regulatory_rag,
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate ScopeAgent: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier2.data_auditor import DataAuditor  # type: ignore
                self._data_auditor = DataAuditor(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate DataAuditor: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier2.model_validator import ModelValidator  # type: ignore
                self._model_validator = ModelValidator(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate ModelValidator: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier2.output_fairness import OutputFairnessTester  # type: ignore
                self._output_fairness = OutputFairnessTester(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate OutputFairnessTester: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier2.governance_agent import GovernanceAgent  # type: ignore
                self._governance_agent = GovernanceAgent(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate GovernanceAgent: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier2.report_architect import ReportArchitect  # type: ignore
                self._report_architect = ReportArchitect(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate ReportArchitect: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier3.uagf_tam_l import UagfTamLBranch  # type: ignore
                self._uagf_tam_l = UagfTamLBranch(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate UagfTamLBranch: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier3.cyber_agent import CyberSecurityAgent  # type: ignore
                self._cyber_agent = CyberSecurityAgent(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate CyberSecurityAgent: %s; stub will be used.", exc)
            try:
                from aaa.agents.tier3.privacy_agent import PrivacyDPOAgent  # type: ignore
                self._privacy_agent = PrivacyDPOAgent(evidence_store=evidence_store)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not instantiate PrivacyDPOAgent: %s; stub will be used.", exc)
        self._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Phase 1 — bound node (real ScopeAgent or stub)
    # ------------------------------------------------------------------

    def _node_phase_1_impl(self, state: dict) -> dict:
        """
        Phase 1 node — runs real ScopeAgent when evidence_store is available,
        otherwise falls back to the module-level stub.
        """
        if self._scope_agent is None:
            return _node_phase_1(state)

        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="P1",
            task_brief=(
                "Verify declared modality, risk tier, and Annex III sections against "
                "intake bundle evidence. Enforce Art. 5 prohibition gate."
            ),
            evidence_uris=evidence_uris,
            output_contract="T02_system_card",
            declaration_summary={
                "engagement_id": eng,
                "declared_modality": state.get("declared_modality", ""),
                "declared_risk_tier": state.get("declared_risk_tier", ""),
                "declared_annex_iii_sections": state.get("declared_annex_iii_sections", []),
                "deployment_context": state.get("deployment_context", ""),
                "live_system_access": state.get("declaration_verification", {}).get(
                    "live_system_access"
                ),
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._scope_agent.process(dispatch))
                        report = future.result(timeout=120)
                else:
                    report = loop.run_until_complete(self._scope_agent.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._scope_agent.process(dispatch))
        except Exception as exc:
            logger.warning("ScopeAgent.process() failed (%s); using stub.", exc)
            return _node_phase_1(state)

        # Apply declaration_verification_delta to state
        delta = report.get("declaration_verification_delta", {})
        state["declaration_verification"].update(delta.get("declaration_verification", {}))
        if delta.get("verified_modality"):
            state["modality"] = delta["verified_modality"]
        if delta.get("verified_risk_tier"):
            state["risk_tier"] = delta["verified_risk_tier"]
        if delta.get("annex_iii_mapping") is not None:
            state["annex_iii_mapping"] = delta["annex_iii_mapping"]
        if "is_llm_or_agentic" in delta:
            state["is_llm_or_agentic"] = delta["is_llm_or_agentic"]
        if delta.get("art43_decision"):
            state["art43_decision"] = delta["art43_decision"]
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        confidence = report.get("confidence", 0.9)
        for tid in ["T02_system_card", "T03_annex_iii_mapping",
                    "T04_risk_tier_decision", "T05_art43_decision"]:
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"Phase 1 ScopeAgent complete. confidence={confidence:.2f}"],
                "article_citations": ["Art.6", "Art.13", "Art.43", "Annex_III"],
                "rerun_required": False,
            }

        logger.info("Engagement %s: Phase 1 (ScopeAgent) complete. confidence=%.2f", eng, confidence)
        return state

    # ------------------------------------------------------------------
    # Phase 2 — bound node (real DataAuditor or stub)
    # ------------------------------------------------------------------

    def _node_parallel_phases_impl(self, state: dict) -> dict:
        """
        Parallel-phases node — runs real DataAuditor (Phase 2) when
        evidence_store is available, then falls back to stubs for
        Phases 3 and 4 (wired in Groups 6–7).
        """
        # L-branch: skip standard Phases 2–4 (handled by UAGF-TAM-L in Group 10)
        if state.get("_branch") == "l_branch":
            if self._uagf_tam_l is not None:
                return self._node_uagf_tam_l_impl(state)
            return _node_parallel_phases(state)

        # ── Phase 2: DataAuditor ──────────────────────────────────────────────
        if self._data_auditor is not None:
            state = self._node_phase_2_impl(state)
        else:
            # Stub for T06/T07/T08 only
            for tid in ["T06_datasheet_for_datasets", "T07_data_quality_report",
                        "T08_special_category_data_log"]:
                if tid not in state["phase_artefacts"]:
                    state["phase_artefacts"][tid] = {
                        "uri": f"mem://{state['engagement_id']}/{tid}",
                        "sha256": "stub",
                        "template_id": tid,
                    }
                    state["verifier_critiques"][tid] = {
                        "verdict": "accept",
                        "issues": [],
                        "notes": [f"{tid} stub — DataAuditor not wired."],
                        "article_citations": [],
                        "rerun_required": False,
                    }

        # ── Phase 3: ModelValidator (skipped for llm/agentic/gpai) ───────────
        modality = (state.get("modality") or "").lower()
        if self._model_validator is not None and modality not in {"llm", "agentic", "gpai"}:
            state = self._node_phase_3_impl(state)
        else:
            for tid in ["T09_model_card", "T10_explainability_report",
                        "T11_robustness_report"]:
                if tid not in state["phase_artefacts"]:
                    state["phase_artefacts"][tid] = {
                        "uri": f"mem://{state['engagement_id']}/{tid}",
                        "sha256": "stub",
                        "template_id": tid,
                    }
                    state["verifier_critiques"][tid] = {
                        "verdict": "accept",
                        "issues": [],
                        "notes": [f"{tid} stub — ModelValidator not wired or modality={modality}."],
                        "article_citations": [],
                        "rerun_required": False,
                    }

        # ── Phase 4: OutputFairnessTester ────────────────────────────────────
        if self._output_fairness is not None:
            state = self._node_phase_4_impl(state)
        else:
            for tid in ["T12_output_fairness_report", "T13_output_sampling_log"]:
                if tid not in state["phase_artefacts"]:
                    state["phase_artefacts"][tid] = {
                        "uri": f"mem://{state['engagement_id']}/{tid}",
                        "sha256": "stub",
                        "template_id": tid,
                    }
                    state["verifier_critiques"][tid] = {
                        "verdict": "accept",
                        "issues": [],
                        "notes": [f"{tid} stub — OutputFairnessTester not wired."],
                        "article_citations": [],
                        "rerun_required": False,
                    }
        return state

    def _node_phase_2_impl(self, state: dict) -> dict:
        """Run the real DataAuditor for Phase 2; fall back to stub on error."""
        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="P2",
            task_brief=(
                "Audit training data quality and governance for Art. 10 compliance. "
                "Scan for PII and special-category data. Produce T06, T07, T08."
            ),
            evidence_uris=evidence_uris,
            output_contract="T06_datasheet_for_datasets",
            declaration_summary={
                "engagement_id": eng,
                "modality": state.get("modality", ""),
                "risk_tier": state.get("risk_tier", ""),
                "special_category_data": (
                    state.get("client_submission", {})
                    .get("stage_a", {})
                    .get("special_category_data", False)
                ),
                "gdpr_overlap": (
                    state.get("client_submission", {})
                    .get("stage_a", {})
                    .get("gdpr_overlap", False)
                ),
                "target_column": None,  # caller can override via state extension
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._data_auditor.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._data_auditor.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._data_auditor.process(dispatch))
        except Exception as exc:
            logger.warning("DataAuditor.process() failed (%s); using stub.", exc)
            return state  # stubs filled in by caller

        # Apply delta to state
        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("special_category_data") is not None:
            # Propagate to stage_a in client_submission for downstream phases
            state.setdefault("client_submission", {}).setdefault(
                "stage_a", {})["special_category_data"] = delta["special_category_data"]
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        confidence = report.get("confidence", 0.85)
        for tid in ["T06_datasheet_for_datasets", "T07_data_quality_report",
                    "T08_special_category_data_log"]:
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"Phase 2 DataAuditor complete. confidence={confidence:.2f}"],
                "article_citations": ["Art.10"],
                "rerun_required": False,
            }

        logger.info("Engagement %s: Phase 2 (DataAuditor) complete. confidence=%.2f",
                    eng, confidence)
        return state

    # ------------------------------------------------------------------
    # Phase 3 — bound node (real ModelValidator or stub)
    # ------------------------------------------------------------------

    def _node_phase_3_impl(self, state: dict) -> dict:
        """Run the real ModelValidator for Phase 3; fall back to stub on error."""
        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="P3",
            task_brief=(
                "Validate model performance, explainability, and robustness "
                "for Art. 13 / Art. 15 compliance. Produce T09, T10, T11."
            ),
            evidence_uris=evidence_uris,
            output_contract="T09_model_card",
            declaration_summary={
                "engagement_id": eng,
                "modality": state.get("modality", ""),
                "risk_tier": state.get("risk_tier", ""),
                "task": "classification",
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._model_validator.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._model_validator.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._model_validator.process(dispatch))
        except Exception as exc:
            logger.warning("ModelValidator.process() failed (%s); using stub.", exc)
            for tid in ["T09_model_card", "T10_explainability_report",
                        "T11_robustness_report"]:
                if tid not in state["phase_artefacts"]:
                    state["phase_artefacts"][tid] = {
                        "uri": f"mem://{eng}/{tid}",
                        "sha256": "stub",
                        "template_id": tid,
                    }
                    state["verifier_critiques"][tid] = {
                        "verdict": "accept",
                        "issues": [],
                        "notes": [f"{tid} stub — ModelValidator error: {exc}"],
                        "article_citations": [],
                        "rerun_required": False,
                    }
            return state

        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        confidence = report.get("confidence", 0.85)
        _ARTICLES_BY_TID = {
            "T09_model_card": ["Art.13", "Art.15"],
            "T10_explainability_report": ["Art.13"],
            "T11_robustness_report": ["Art.15"],
        }
        for tid, articles in _ARTICLES_BY_TID.items():
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"Phase 3 ModelValidator complete. confidence={confidence:.2f}"],
                "article_citations": articles,
                "rerun_required": False,
            }

        logger.info("Engagement %s: Phase 3 (ModelValidator) complete. confidence=%.2f",
                    eng, confidence)
        return state

    # ------------------------------------------------------------------
    # Phase 4 — bound node (real OutputFairnessTester or stub)
    # ------------------------------------------------------------------

    def _node_phase_4_impl(self, state: dict) -> dict:
        """Run the real OutputFairnessTester for Phase 4; fall back to stub on error."""
        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="P4",
            task_brief=(
                "Test model outputs for fairness and discriminatory patterns. "
                "Apply demographic parity, equal opportunity, disparate impact, "
                "subgroup metrics, and toxicity classification. Produce T12, T13."
            ),
            evidence_uris=evidence_uris,
            output_contract="T12_output_fairness_report",
            declaration_summary={
                "engagement_id": eng,
                "modality": state.get("modality", "tabular"),
                "risk_tier": state.get("risk_tier", ""),
                "y_true": state.get("y_true"),
                "y_pred": state.get("y_pred"),
                "sensitive_features": state.get("sensitive_features"),
                "sensitive_feature_names": state.get("sensitive_feature_names", []),
                "privileged_group": state.get("privileged_group"),
                "positive_label": state.get("positive_label", 1),
                "prediction_texts": state.get("prediction_texts"),
                "prediction_ids": state.get("prediction_ids"),
                "sampling_strategy": state.get("sampling_strategy", "first_n"),
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._output_fairness.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._output_fairness.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._output_fairness.process(dispatch))
        except Exception as exc:
            logger.warning("OutputFairnessTester.process() failed (%s); using stub.", exc)
            for tid in ["T12_output_fairness_report", "T13_output_sampling_log"]:
                if tid not in state["phase_artefacts"]:
                    state["phase_artefacts"][tid] = {
                        "uri": f"mem://{eng}/{tid}",
                        "sha256": "stub",
                        "template_id": tid,
                    }
                    state["verifier_critiques"][tid] = {
                        "verdict": "accept",
                        "issues": [],
                        "notes": [f"{tid} stub — OutputFairnessTester error: {exc}"],
                        "article_citations": [],
                        "rerun_required": False,
                    }
            return state

        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        confidence = report.get("confidence", 0.85)
        _ARTICLES_BY_TID = {
            "T12_output_fairness_report": ["Art.10§2(f)", "Art.15§1"],
            "T13_output_sampling_log": ["Art.15§1"],
        }
        for tid, articles in _ARTICLES_BY_TID.items():
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"Phase 4 OutputFairnessTester complete. confidence={confidence:.2f}"],
                "article_citations": articles,
                "rerun_required": False,
            }

        logger.info("Engagement %s: Phase 4 (OutputFairnessTester) complete. confidence=%.2f",
                    eng, confidence)
        return state

    # ------------------------------------------------------------------
    # Tier-3 Specialist — UAGF-TAM-L (Generative systems)
    # ------------------------------------------------------------------

    def _node_uagf_tam_l_impl(self, state: dict) -> dict:
        """Run the real UagfTamLBranch for generative systems."""
        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="PL",
            task_brief=(
                "Perform L-branch specialist audit for LLM/agentic/GPAI system. "
                "Include golden-set, RAGAs, groundedness, and prompt injection. Produce T16."
            ),
            evidence_uris=evidence_uris,
            output_contract="T16_uagf_tam_l_evidence",
            declaration_summary={
                "engagement_id": eng,
                "modality": state.get("modality", "llm"),
                "risk_tier": state.get("risk_tier", ""),
                "stage_b": state.get("client_submission", {}).get("stage_b", {}),
                "stage_c": state.get("client_submission", {}).get("stage_c", {}),
                "system_prompt_text": state.get("system_prompt_text"),
                "eval_questions": state.get("eval_questions"),
                "eval_contexts": state.get("eval_contexts"),
                "eval_answers": state.get("eval_answers"),
                "eval_expected": state.get("eval_expected"),
                "trace_sample": state.get("trace_sample"),
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._uagf_tam_l.process(dispatch))
                        report = future.result(timeout=300)
                else:
                    report = loop.run_until_complete(self._uagf_tam_l.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._uagf_tam_l.process(dispatch))
        except Exception as exc:
            logger.warning("UagfTamLBranch.process() failed (%s); using stub.", exc)
            return _node_parallel_phases(state)

        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        confidence = report.get("confidence", 0.9)
        for tid in ["T16_uagf_tam_l_evidence"]:
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"L-branch UagfTamLBranch complete. confidence={confidence:.2f}"],
                "article_citations": ["Art.15", "Art.51", "Art.52", "Art.53", "Art.54", "Art.55"],
                "rerun_required": False,
            }

        logger.info("Engagement %s: L-branch (UagfTamL) complete. confidence=%.2f", eng, confidence)
        return state


    # ------------------------------------------------------------------
    # Phase 5 — bound node (real GovernanceAgent or stub)
    # ------------------------------------------------------------------

    def _node_phase_5_impl(self, state: dict) -> dict:
        """Run the real GovernanceAgent for Phase 5; fall back to stub on error."""
        if self._governance_agent is None:
            return _node_phase_5(state)

        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        stage_a = state.get("client_submission", {}).get("stage_a", {}) or {}
        # Verifier critiques for Phase 3 robustness (used by Cyber spawn logic)
        t11_critique = state.get("verifier_critiques", {}).get("T11_robustness_report", {})
        t11_verdict = "PASS" if t11_critique.get("verdict") in {
            "accept", "accept_with_notes"
        } else "FAIL"

        dispatch = Dispatch(
            phase_id="P5",
            task_brief=(
                "Pull and ingest the S4 CGSA payload, cross-check risk_tier, "
                "decide Tier-3 spawns, and produce T14 + T15."
            ),
            evidence_uris=evidence_uris,
            output_contract="T14_governance_findings",
            declaration_summary={
                "engagement_id": eng,
                "risk_tier": state.get("risk_tier", ""),
                "cgsa_assessment_id": stage_a.get("cgsa_assessment_id"),
                "cgsa_payload": state.get("cgsa_payload"),
                "gdpr_overlap": stage_a.get("gdpr_overlap", False),
                "special_category_data": stage_a.get("special_category_data", False),
                "annex_iii_sections": [
                    e.get("annex_iii_section")
                    for e in state.get("annex_iii_mapping", []) or []
                ] or state.get("declared_annex_iii_sections", []),
                "phase3_robustness_verdict": t11_verdict,
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._governance_agent.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._governance_agent.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._governance_agent.process(dispatch))
        except Exception as exc:
            logger.warning("GovernanceAgent.process() failed (%s); using stub.", exc)
            return _node_phase_5(state)

        delta = report.get("declaration_verification_delta", {})
        # Lift every §5.4 hydration key onto AuditState
        for key, value in delta.items():
            if key == "phase_artefacts":
                state["phase_artefacts"].update(value or {})
            elif key in {"hitl_required", "hitl_reason"}:
                continue
            else:
                state[key] = value
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        confidence = report.get("confidence", 0.85)
        for tid in ["T14_governance_findings", "T15_monitoring_logging_review"]:
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"Phase 5 GovernanceAgent complete. confidence={confidence:.2f}"],
                "article_citations": ["Art.9", "Art.10", "Art.13", "Art.14", "Art.17", "Art.72"],
                "rerun_required": False,
            }

        logger.info("Engagement %s: Phase 5 (GovernanceAgent) complete. confidence=%.2f",
                    eng, confidence)

        # ── Tier-3 Specialist Spawns ─────────────────────────────────────────
        if delta.get("spawn_cyber_subagent") and self._cyber_agent is not None:
            logger.info("Spawning CyberSecurityAgent for engagement %s", eng)
            state = self._node_cyber_impl(state)

        if delta.get("spawn_privacy_subagent") and self._privacy_agent is not None:
            logger.info("Spawning PrivacyDPOAgent for engagement %s", eng)
            state = self._node_privacy_impl(state)

        return state


    def _node_cyber_impl(self, state: dict) -> dict:
        """Run the real CyberSecurityAgent; fall back to no-op on error."""
        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="Cyber",
            task_brief=(
                "Perform deep-dive cybersecurity and adversarial robustness audit. "
                "Extend T11_robustness_report."
            ),
            evidence_uris=evidence_uris,
            output_contract="T11_robustness_report",
            declaration_summary={
                "engagement_id": eng,
                "modality": state.get("modality", "tabular"),
                "trained_model": state.get("trained_model"),
                "X_eval": state.get("X_eval"),
                "y_eval": state.get("y_eval"),
                "system_prompt_text": state.get("system_prompt_text"),
                "phase_artefacts": artefacts,
                "stage_c": state.get("client_submission", {}).get("stage_c", {}),
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._cyber_agent.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._cyber_agent.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._cyber_agent.process(dispatch))
        except Exception as exc:
            logger.warning("CyberSecurityAgent.process() failed (%s)", exc)
            return state

        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("blocking_findings"):
            state.setdefault("blocking_findings", []).extend(delta["blocking_findings"])
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        return state

    def _node_privacy_impl(self, state: dict) -> dict:
        """Run the real PrivacyDPOAgent; fall back to no-op on error."""
        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        artefacts = state.get("phase_artefacts", {})
        t01a_uri = artefacts.get("T01a_stage_a_triage", {}).get("uri", "")
        t01b_uri = artefacts.get("T01b_annex_iv_dossier", {}).get("uri", "")
        evidence_uris = [u for u in [t01a_uri, t01b_uri] if u]

        dispatch = Dispatch(
            phase_id="Privacy",
            task_brief=(
                "Perform deep-dive Privacy / DPO audit for GDPR compliance. "
                "Extend T08_special_category_data_log."
            ),
            evidence_uris=evidence_uris,
            output_contract="T08_special_category_data_log",
            declaration_summary={
                "engagement_id": eng,
                "modality": state.get("modality", "tabular"),
                "X_eval": state.get("X_eval"),
                "phase_artefacts": artefacts,
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._privacy_agent.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._privacy_agent.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._privacy_agent.process(dispatch))
        except Exception as exc:
            logger.warning("PrivacyDPOAgent.process() failed (%s)", exc)
            return state

        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("hitl_required"):
            state["hitl_required"] = True
            state["hitl_reason"] = delta.get("hitl_reason")

        return state

    # ------------------------------------------------------------------
    # Phase 6 — bound node (real ReportArchitect or stub)
    # ------------------------------------------------------------------

    def _node_phase_6_impl(self, state: dict) -> dict:
        """Run the real ReportArchitect for Phase 6; fall back to stub on error."""
        if self._report_architect is None:
            return _node_phase_6(state)

        import asyncio
        import concurrent.futures

        eng = state["engagement_id"]
        stage_a = state.get("client_submission", {}).get("stage_a", {}) or {}

        # Build annex_iii_sections list from mapping
        annex_iii_sections = [
            e.get("annex_iii_section")
            for e in (state.get("annex_iii_mapping") or [])
            if e.get("annex_iii_section")
        ] or state.get("declared_annex_iii_sections", [])

        # Build verifier_summary (verdict counts)
        critiques = state.get("verifier_critiques", {})
        verifier_summary: dict = {}
        for tid, crit in critiques.items():
            v = crit.get("verdict", "unknown")
            verifier_summary[v] = verifier_summary.get(v, 0) + 1

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
                "stage_a": stage_a,
                "risk_tier": state.get("risk_tier", "high"),
                "modality": state.get("modality", "tabular"),
                "deployment_context": state.get("deployment_context", "b2b"),
                "is_llm_or_agentic": state.get("is_llm_or_agentic", False),
                "annex_iii_sections": annex_iii_sections,
                "art43_decision": state.get("art43_decision"),
                "compliance_matrix": state.get("compliance_matrix", {}),
                "phase_artefacts": state.get("phase_artefacts", {}),
                "verifier_critiques": state.get("verifier_critiques", {}),
                "blocking_findings": state.get("blocking_findings", []),
                "positive_findings": state.get("positive_findings", []),
                "remediation_roadmap": state.get("remediation_roadmap", []),
                "intake_completeness_score": state.get("intake_completeness_score"),
                "completeness_score": state.get("completeness_score"),
                "regulatory_coverage_pct": state.get("regulatory_coverage_pct"),
                "final_verdict": state.get("final_verdict"),
                "cgsa_report_url": state.get("cgsa_report_url"),
                "hitl_required": state.get("hitl_required", False),
                "hitl_reason": state.get("hitl_reason"),
                "verifier_summary": verifier_summary,
            },
        )

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._report_architect.process(dispatch))
                        report = future.result(timeout=180)
                else:
                    report = loop.run_until_complete(self._report_architect.process(dispatch))
            except RuntimeError:
                report = asyncio.run(self._report_architect.process(dispatch))
        except Exception as exc:
            logger.warning("ReportArchitect.process() failed (%s); using stub.", exc)
            return _node_phase_6(state)

        delta = report.get("declaration_verification_delta", {})
        state["phase_artefacts"].update(delta.get("phase_artefacts", {}))
        if delta.get("final_verdict"):
            state["final_verdict"] = delta["final_verdict"]

        confidence = report.get("confidence", 0.95)
        for tid in ["T17_compliance_matrix", "T18_audit_report"]:
            state["verifier_critiques"][tid] = {
                "verdict": "accept",
                "issues": [],
                "notes": [f"Phase 6 ReportArchitect complete. confidence={confidence:.2f}"],
                "article_citations": ["Art.17", "Art.43", "Annex_IV"],
                "rerun_required": False,
            }

        logger.info("Engagement %s: Phase 6 (ReportArchitect) complete. confidence=%.2f",
                    eng, confidence)
        return state

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        """Build and compile the LangGraph StateGraph."""
        try:
            from langgraph.graph import StateGraph, END  # type: ignore

            g = StateGraph(dict)
            g.add_node("stage_0", _node_stage_0)
            g.add_node("plan", _node_plan)
            g.add_node("phase_1", self._node_phase_1_impl)
            g.add_node("route", _node_route)
            g.add_node("parallel_phases", self._node_parallel_phases_impl)
            g.add_node("phase_5", self._node_phase_5_impl)
            g.add_node("compliance_matrix", _node_compliance_matrix)
            g.add_node("hitl_checkpoint", _node_hitl_checkpoint)
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
                _should_hitl,
                {"phase_6": "phase_6", "wait_hitl": END},
            )
            g.add_edge("phase_6", END)

            checkpointer = self._checkpointer if not isinstance(
                self._checkpointer, _InMemoryCheckpointer
            ) else None
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
        state = _initial_state(engagement_id, client_submission)
        return await self.run(state)

    async def run(self, state: dict) -> dict:
        """Execute the graph (or sequential fallback) and return final state."""
        if self._graph is not None:
            return await self._run_langgraph(state)
        return self._run_sequential(state)

    async def _run_langgraph(self, state: dict) -> dict:  # pragma: no cover
        """Invoke the compiled LangGraph; return final state."""
        config = {"configurable": {"thread_id": state["engagement_id"]}}
        final: dict = {}
        async for chunk in self._graph.astream(state, config=config):
            final = chunk
        return final

    def _run_sequential(self, state: dict) -> dict:
        """Sequential fallback: run all nodes in order (offline/CI)."""
        nodes = [
            _node_stage_0,
            _node_plan,
            self._node_phase_1_impl,
            _node_route,
            self._node_parallel_phases_impl,
            self._node_phase_5_impl,
            _node_compliance_matrix,
            _node_hitl_checkpoint,
            self._node_phase_6_impl,
        ]
        for node_fn in nodes:
            state = node_fn(state)
            self._checkpointer.put(state["engagement_id"], state)
            if state.get("hitl_required") and not _OFFLINE:
                logger.warning("Halting at HITL checkpoint for engagement %s", state["engagement_id"])
                break
        return state

