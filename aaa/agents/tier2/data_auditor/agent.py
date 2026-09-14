"""The DataAuditor class — Phase 2 data-governance coordinator."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.common import load_intake
from aaa.agents.tier2.data_auditor.analysis import run_analysis
from aaa.agents.tier2.data_auditor.artefacts import build_and_store_artefacts
from aaa.agents.tier2.data_auditor.context import gather_context, gather_t06_evidence
from aaa.agents.tier2.data_auditor.llm import run_llm_synthesis
from aaa.agents.tier2.data_auditor.report import assemble_report
from aaa.platform.evidence import EvidenceStore
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class DataAuditor(BaseAgent):
    """Phase 2 — Data Governance Auditor.

    Verifies data quality, completeness, and special-category-data handling
    against EU AI Act Art. 10 requirements.  Emits T06, T07, T08 artefacts.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None, regulatory_rag: Any | None = None):
        super().__init__(
            name="DataAuditor",
            model=resolve_model("DataAuditor", model),
            service_tier=resolve_service_tier("DataAuditor", service_tier),
        )
        self.store, self.rag = evidence_store, regulatory_rag

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run the Phase 2 data governance audit and return a Report.

        :param message: Dispatch with T01a/T01b URIs and the declaration summary.
        :returns: Report with the T06 artefact URI and the verification delta
            (updated ``special_category_data`` when the PII scan overrides
            the declaration).
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]

        t01a, t01b = load_intake(self.store, message.get("evidence_uris", []))
        ctx = run_analysis(self, t01b, decl)
        ctx["evidence_uris"] = message.get("evidence_uris", [])
        ctx["client_doc_hits"], regulatory_hits = gather_context(self, decl, engagement_id)
        ctx["t06_found"] = gather_t06_evidence(decl, engagement_id, t01b)

        # dict() cast: pyright will not assign the Dispatch TypedDict to dict.
        llm_summary, prompt_note = await run_llm_synthesis(
            self, dict(message), decl, engagement_id,
            tool_outputs={
                "profile_result": ctx["profile_result"],
                "missingness": ctx["miss_result"],
                "class_balance": ctx["balance_result"],
                "pii_scan": ctx["pii_result"],
                # F10: drift ran on every Phase 2 dispatch and was shown to
                # nobody — the model at call #003 asked for the tool by name.
                "drift_test": ctx["drift_result"],
                "overall_quality_verdict": ctx["verdict"],
            },
            client_doc_hits=ctx["client_doc_hits"], regulatory_hits=regulatory_hits)

        uris = build_and_store_artefacts(
            self, engagement_id, t01a, t01b, decl, ctx, prompt_note)
        return assemble_report(ctx, uris, llm_summary, prompt_note)
