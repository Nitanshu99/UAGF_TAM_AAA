"""The OutputFairnessTester class — Phase 4 fairness-testing coordinator."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.common import load_intake
from aaa.agents.tier2.output_fairness.artefacts import build_and_store_artefacts
from aaa.agents.tier2.output_fairness.delta import build_delta
from aaa.agents.tier2.output_fairness.inputs import resolve_inputs
from aaa.agents.tier2.output_fairness.llm import run_llm_synthesis
from aaa.agents.tier2.output_fairness.report import assemble_report
from aaa.agents.tier2.output_fairness.suite import run_fairness_suite
from aaa.agents.tier2.output_fairness.toxicity import run_toxicity
from aaa.agents.tier2.output_fairness.verdicts import apply_verdict_findings
from aaa.platform.evidence import EvidenceStore


class OutputFairnessTester(BaseAgent):
    """Phase 4 — Output Fairness Tester.

    Verifies model outputs for bias and discriminatory patterns against
    EU AI Act Art. 10 §2(f) / Art. 15 §1 requirements.  Emits T12, T13.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None, regulatory_rag: Any | None = None):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="OutputFairnessTester",
            model=resolve_model("OutputFairnessTester", model),
            service_tier=resolve_service_tier("OutputFairnessTester", service_tier),
        )
        self.store, self.rag = evidence_store, regulatory_rag

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run Phase 4 output fairness testing and return a Report.

        :param message: Dispatch whose ``declaration_summary`` includes at
            minimum ``engagement_id`` and ``modality``; predictions, labels
            and sensitive features may be injected directly or resolved from
            the declared evaluation artefacts.
        :returns: Report with the T12 artefact URI and the verification delta.
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]
        modality: str = (decl.get("modality") or "tabular").lower()

        _t01a, t01b = load_intake(self.store, message.get("evidence_uris", []))
        inp = resolve_inputs(self.store, decl, t01b, modality)
        suite = run_fairness_suite(inp)
        tox_result = run_toxicity(inp, modality)
        skipped_reason = apply_verdict_findings(inp, suite)
        # dict() casts: pyright will not assign the Dispatch TypedDict to dict.
        llm = await run_llm_synthesis(self, dict(message), decl, engagement_id,
                                      suite, tox_result)
        uris, t13 = build_and_store_artefacts(self, engagement_id, modality, inp,
                                              suite, tox_result, skipped_reason, llm,
                                              decl.get("risk_tier"))
        delta = build_delta(dict(message), inp, suite, t13, uris)
        return assemble_report(suite, tox_result, uris, delta, llm)
