"""The ScopeAgent class — Phase 1 declaration verification coordinator."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.common import load_intake
from aaa.agents.tier2.scope_agent.artefacts import build_and_store_artefacts
from aaa.agents.tier2.scope_agent.checks import build_description
from aaa.agents.tier2.scope_agent.context import computed_evidence
from aaa.agents.tier2.scope_agent.llm import gather_context, run_llm_synthesis
from aaa.agents.tier2.scope_agent.report import assemble_report
from aaa.agents.tier2.scope_agent.verify import run_verification
from aaa.platform.evidence import EvidenceStore
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class ScopeAgent(BaseAgent):
    """Phase 1 — Scope and Risk Classifier.

    Verifies the client's declared values from Stage A, emits
    ``declaration_verification``, and writes T02–T05 to the Evidence Store.
    Any mismatch sets ``hitl_required=True`` in the returned state update.
    """

    def __init__(self, evidence_store: EvidenceStore, regulatory_rag: Any | None = None,
                 model: str | None = None, service_tier: str | None = None):
        super().__init__(
            name="ScopeAgent",
            model=resolve_model("ScopeAgent", model),
            service_tier=resolve_service_tier("ScopeAgent", service_tier),
        )
        self.store, self.rag = evidence_store, regulatory_rag

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run Phase 1 verification and return a Report.

        :param message: Dispatch with T01a/T01b URIs and the declaration summary.
        :returns: Report with the T02 artefact URI and the verification delta.
        :raises aaa.agents.tier2.scope_agent.errors.ScopeAgentError:
            When an Art. 5 prohibition is detected.
        """
        decl = message.get("declaration_summary", {})
        engagement_id = decl.get("engagement_id") or message["phase_id"]
        t01a, t01b = load_intake(self.store, message["evidence_uris"])
        system_desc = build_description(t01a, t01b)

        # dict() casts: pyright will not assign the Dispatch TypedDict to dict.
        ctx = run_verification(self, t01a, t01b, decl, dict(message),
                               engagement_id, system_desc)
        ctx["client_doc_hits"], regulatory_hits = gather_context(self, decl, engagement_id)
        llm_summary, prompt_note = await run_llm_synthesis(
            self, dict(message), decl, engagement_id,
            computed_evidence=computed_evidence(ctx, system_desc),
            client_doc_hits=ctx["client_doc_hits"], regulatory_hits=regulatory_hits)

        uris = build_and_store_artefacts(self, ctx, llm_summary, prompt_note)
        return assemble_report(ctx, uris, llm_summary, prompt_note)
