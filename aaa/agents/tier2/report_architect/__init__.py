"""ReportArchitect — Tier-2 Phase 6 Report Architect (§3.2 #9, §4.5).

Receives a :class:`~aaa.agents.base.Dispatch` from the Orchestrator and

1. builds the T17 compliance-matrix payload from ``AuditState`` fields
   threaded through ``declaration_summary``,
2. renders + persists T17 via ``template_render``,
3. builds the T18 audit-report payload, embedding T17 by URI reference,
4. renders the risk heatmap / maturity radar and the PDF + JSON report, and
5. emits a :class:`~aaa.agents.base.Report` whose delta carries both
   artefact refs and the final verdict.

Phase 6 uses a prompt-driven synthesis path and falls back to deterministic
assembly when the LLM call fails.
"""
from __future__ import annotations

from aaa.agents.tier2.report_architect.agent import ReportArchitect
from aaa.agents.tier2.report_architect.constants import kpi_band as _kpi_band
from aaa.agents.tier2.report_architect.management import (
    management_response_shell as _management_response_shell,
)
from aaa.agents.tier2.report_architect.opinion import auditor_opinion as _auditor_opinion

__all__ = ["ReportArchitect", "_auditor_opinion", "_kpi_band",
           "_management_response_shell"]
