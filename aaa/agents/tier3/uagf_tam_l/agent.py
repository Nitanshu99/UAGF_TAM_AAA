"""The UagfTamLBranch class — generative-modality audit coordinator."""
from __future__ import annotations

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier3.uagf_tam_l.ragas_run import derive_verdict, run_golden_set
from aaa.agents.tier3.uagf_tam_l.run import run_uagf_tam_l_branch
from aaa.platform.evidence import EvidenceStore
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class UagfTamLBranch(BaseAgent):
    """UAGF-TAM-L Branch Agent — RAG / Agentic / GPAI specific audits."""

    #: kept as methods for backwards compatibility with earlier call sites
    _run_golden_set = staticmethod(run_golden_set)
    _derive_verdict = staticmethod(derive_verdict)

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None):
        super().__init__(
            name="UAGF-TAM-L",
            model=resolve_model("UAGF-TAM-L", model),
            service_tier=resolve_service_tier("UAGF-TAM-L", service_tier),
        )
        self.store = evidence_store

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run the UAGF-TAM-L audit and return a Report.

        :param message: Dispatch carrying the declaration summary with
            evaluation inputs (questions/contexts/answers/expected).
        :returns: Report whose delta registers T16.
        """
        return await run_uagf_tam_l_branch(self, message)
