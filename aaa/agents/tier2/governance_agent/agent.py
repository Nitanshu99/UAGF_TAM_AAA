"""The GovernanceAgent class — Phase 5 workflow coordinator."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.common import load_intake
from aaa.agents.tier2.governance_agent.artefacts import build_and_store_artefacts
from aaa.agents.tier2.governance_agent.context import gather_context
from aaa.agents.tier2.governance_agent.enrich import enrich_remediation_roadmap
from aaa.agents.tier2.governance_agent.ingest import acquire_and_validate
from aaa.agents.tier2.governance_agent.llm import run_llm_synthesis
from aaa.agents.tier2.governance_agent.report import assemble_report
from aaa.agents.tier2.governance_agent.spawns import decide_tier3_spawns
from aaa.platform.evidence import EvidenceStore
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class GovernanceAgent(BaseAgent):
    """Phase 5 — Governance Agent.

    Ingests the upstream S4 CGSA payload, lifts the §5.4 hand-off surface
    into ``AuditState`` and emits T14 + T15 artefacts.  The Phase 5 verdict
    is driven primarily by ``aaa_phase5_handoff.phase5_verdict``; CSP failure
    forces FAIL.
    """

    #: kept as a staticmethod for test access (tests/unit/test_remediation_assignment.py)
    _enrich_remediation_roadmap = staticmethod(enrich_remediation_roadmap)

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None, regulatory_rag: Any | None = None):
        super().__init__(
            name="GovernanceAgent",
            model=resolve_model("GovernanceAgent", model),
            service_tier=resolve_service_tier("GovernanceAgent", service_tier),
        )
        self.store, self.rag = evidence_store, regulatory_rag

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run Phase 5 governance ingestion and return a Report.

        :param message: Dispatch whose ``declaration_summary`` must include
            ``engagement_id`` and should include ``risk_tier``,
            ``cgsa_assessment_id``, GDPR flags, and Annex III sections.
        :returns: The Phase 5 ``Report`` (or an HITL escalation report).
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]

        outcome = acquire_and_validate(decl, engagement_id)
        if not isinstance(outcome, tuple):  # escalation Report (TypedDict → plain dict)
            return outcome
        payload, result = outcome

        risk_tier_mismatch = result.state_delta.get("cgsa_risk_tier_match") is False
        spawn = decide_tier3_spawns(decl, result)
        _t01a, t01b = load_intake(self.store, message.get("evidence_uris", []))
        now = datetime.now(timezone.utc).isoformat()

        client_doc_hits, regulatory_hits = gather_context(self, decl, engagement_id)

        # dict() cast: pyright will not assign the Dispatch TypedDict to dict.
        llm_summary, prompt_note = await run_llm_synthesis(
            self, dict(message), decl, engagement_id, payload, result, spawn,
            client_doc_hits, regulatory_hits)

        t14, t15, t14_uri, t15_uri = build_and_store_artefacts(
            self, engagement_id, result, decl, spawn, risk_tier_mismatch,
            now, t01b, llm_summary, prompt_note)

        return assemble_report({
            "result": result, "payload": payload, "spawn": spawn,
            "t14": t14, "t15": t15, "t14_uri": t14_uri, "t15_uri": t15_uri,
            "risk_tier_mismatch": risk_tier_mismatch,
            "evidence_uris": message.get("evidence_uris", []),
            "client_doc_hits": client_doc_hits,
            "llm_summary": llm_summary, "prompt_note": prompt_note,
        })
