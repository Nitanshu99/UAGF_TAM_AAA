"""The ModelValidator class — Phase 3 model-validation coordinator."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.model_validator.run import run_model_validator
from aaa.platform.evidence import EvidenceStore


class ModelValidator(BaseAgent):
    """Phase 3 — Model Validation Agent.

    Verifies model performance, explainability, and adversarial robustness
    against EU AI Act Art. 13 / 15 requirements.  Emits T09, T10, T11.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None, regulatory_rag: Any | None = None):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="ModelValidator",
            model=resolve_model("ModelValidator", model),
            service_tier=resolve_service_tier("ModelValidator", service_tier),
        )
        self.store, self.rag = evidence_store, regulatory_rag

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run Phase 3 model validation and return a Report.

        :param message: Dispatch whose ``declaration_summary`` includes at
            minimum ``engagement_id`` and ``modality``; model / evaluation
            artefacts may be injected directly or declared by URI.
        :returns: Report with the T09 artefact URI and the verification delta.
        """
        return await run_model_validator(self, message)
