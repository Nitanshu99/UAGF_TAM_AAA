"""The ReportArchitect class — Phase 6 report-assembly coordinator."""
from __future__ import annotations

import logging

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.report_architect.run import run_report_architect
from aaa.platform.evidence import EvidenceStore

logger = logging.getLogger(__name__)


class ReportArchitect(BaseAgent):
    """Phase 6 — Report Architect.  Emits T17 and the final T18 report."""

    def __init__(self, evidence_store: EvidenceStore, model: str | None = None,
                 service_tier: str | None = None):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="ReportArchitect",
            model=resolve_model("ReportArchitect", model),
            service_tier=resolve_service_tier("ReportArchitect", service_tier),
        )
        self.store = evidence_store

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Assemble T17 + T18, render the report, and return a Report.

        :param message: Dispatch whose ``declaration_summary`` threads the
            accumulated ``AuditState`` fields (matrix, findings, KPIs).
        :returns: Report with the T18 artefact URI and the final verdict.
        """
        return await run_report_architect(self, message)
