"""The PrivacyDPOAgent class — Tier-3 privacy / DPO review."""
from __future__ import annotations

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier3.privacy_agent.run import run_privacy_audit
from aaa.platform.evidence import EvidenceStore
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class PrivacyDPOAgent(BaseAgent):
    """Tier-3 Privacy / DPO Sub-Agent.

    Justified by Mökander 2023 application-layer privacy audit and Art. 10 §5.
    Extends T08_special_category_data_log.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None):
        super().__init__(
            name="PrivacyDPOAgent",
            model=resolve_model("PrivacyDPOAgent", model),
            service_tier=resolve_service_tier("PrivacyDPOAgent", service_tier),
        )
        self.store = evidence_store

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run the privacy/DPO audit and return a Report.

        :param message: Dispatch with the declaration summary and T08 ref.
        :returns: Report whose delta extends T08.
        """
        return await run_privacy_audit(self, message)
