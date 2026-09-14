"""The CyberSecurityAgent class — Tier-3 independent security review."""
from __future__ import annotations

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier3.cyber_agent.run import run_cyber_audit
from aaa.platform.evidence import EvidenceStore
from aaa.platform.model_registry import resolve_model, resolve_service_tier


class CyberSecurityAgent(BaseAgent):
    """Tier-3 Cybersecurity Sub-Agent.

    Justified by Falco 2021 (independent security review) and Art. 15
    requirements.  Extends T11 with deeper adversarial and injection probes.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None):
        super().__init__(
            name="CyberSecurityAgent",
            model=resolve_model("CyberSecurityAgent", model),
            service_tier=resolve_service_tier("CyberSecurityAgent", service_tier),
        )
        self.store = evidence_store

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Run the cybersecurity audit and return a Report.

        :param message: Dispatch with the declaration summary and T11 ref.
        :returns: Report whose delta extends T11 and may raise blocking findings.
        """
        return await run_cyber_audit(self, message)
