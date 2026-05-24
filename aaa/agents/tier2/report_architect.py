"""
ReportArchitect — Tier-2 Phase 6 Report Architect (§3.2 #9, §4.5).

Receives a ``Dispatch`` from the Orchestrator and performs the following
workflow:

  1. Build the T17 compliance-matrix payload from ``AuditState`` fields
     threaded through ``declaration_summary``.
  2. Render + persist T17 via ``template_render``.
  3. Build the T18 audit-report payload, embedding T17 by URI reference.
  4. Call ``report_render`` to produce the PDF + machine-readable JSON.
  5. Persist the updated T18 (with rendered_report block) via ``template_render``.
  6. Emit ``Report`` whose ``declaration_verification_delta`` carries both
     artefact refs and the final_verdict.

Phase 6 is non-LLM; all logic is deterministic.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.agents.base import BaseAgent, Dispatch, Report
from src.platform.evidence import EvidenceStore
from src.tools.template_render import template_render
from src.tools.report_render import report_render

logger = logging.getLogger(__name__)

# Article → source phase mapping (used to populate T17.articles.source_phase)
_ARTICLE_PHASE: dict[str, str] = {
    "Art.5": "P1", "Art.6": "P1", "Art.9": "P5", "Art.10": "P2",
    "Art.13": "P1", "Art.14": "P3", "Art.15": "P3", "Art.17": "P5",
    "Art.43": "P1", "Art.50": "P1", "Art.72": "P5", "Annex_III": "P1",
    "Annex_IV": "ORCH", "GPAI_51": "L", "GPAI_52": "L", "GPAI_53": "L",
    "GPAI_54": "L", "GPAI_55": "L", "Annex_XI": "L", "Annex_XII": "L",
}
_VALID_PHASES = {"P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIV", "ORCH"}

_KPI_BANDS = [
    (0.90, "PASS"),
    (0.75, "PASS_WITH_OBSERVATIONS"),
    (0.0,  "FAIL"),
]


def _kpi_band(value: float | None, pct: bool = False) -> str | None:
    if value is None:
        return None
    v = value if not pct else value / 100.0
    for threshold, band in _KPI_BANDS:
        if v >= threshold:
            return band
    return "FAIL"


class ReportArchitect(BaseAgent):
    """Phase 6 — Report Architect."""

    def __init__(self, evidence_store: EvidenceStore, model: str = "claude-sonnet-4-5"):
        super().__init__(name="ReportArchitect", model=model)
        self.store = evidence_store

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]
        now = datetime.now(timezone.utc).isoformat()

        # ── 1. Build + render T17 ─────────────────────────────────────────────
        t17 = self._build_t17(engagement_id, decl, now)
        t17_ref = template_render(
            "T17_compliance_matrix", t17,
            engagement_id=engagement_id, phase="phase_6",
            agent_name=self.name, store=self.store,
        )

        # ── 2. Build T18 (without rendered_report yet) ────────────────────────
        t18 = self._build_t18(engagement_id, decl, t17_ref, now)

        # ── 3. Render to PDF + JSON ───────────────────────────────────────────
        rendered = report_render(t18, engagement_id=engagement_id,
                                 store=self.store, agent_name=self.name)
        t18["rendered_report"] = {
            "pdf_uri": rendered.get("pdf_uri"),
            "pdf_bytes_size": rendered.get("pdf_bytes_size"),
            "json_uri": rendered["json_uri"],
            "renderer": rendered.get("renderer"),
        }

        # ── 4. Persist final T18 ──────────────────────────────────────────────
        t18_ref = template_render(
            "T18_audit_report", t18,
            engagement_id=engagement_id, phase="phase_6",
            agent_name=self.name, store=self.store,
        )

        final_verdict = t17.get("final_verdict", "PASS_WITH_OBSERVATIONS")

        return Report(
            phase_id="P6",
            artefact_uri=t18_ref["uri"],
            summary=(
                f"Phase 6 complete. final_verdict={final_verdict}, "
                f"articles={len(t17.get('articles', []))}, "
                f"renderer={rendered.get('renderer')}."
            ),
            confidence=0.95,
            tool_calls=[
                {"tool": "template_render", "result": f"T17 uri={t17_ref['uri']}"},
                {"tool": "report_render", "result": f"renderer={rendered.get('renderer')}"},
                {"tool": "template_render", "result": f"T18 uri={t18_ref['uri']}"},
            ],
            declaration_verification_delta={
                "phase_artefacts": {
                    "T17_compliance_matrix": dict(t17_ref),
                    "T18_audit_report": dict(t18_ref),
                },
                "final_verdict": final_verdict,
            },
        )

    # ------------------------------------------------------------------
    # T17 builder
    # ------------------------------------------------------------------

    def _build_t17(self, engagement_id: str, decl: dict, now: str) -> dict[str, Any]:
        compliance_matrix: dict[str, str] = decl.get("compliance_matrix", {}) or {}
        blocking_findings: list[dict] = decl.get("blocking_findings", []) or []
        phase_artefacts: dict[str, Any] = decl.get("phase_artefacts", {}) or {}
        verifier_critiques: dict[str, Any] = decl.get("verifier_critiques", {}) or {}
        risk_tier: str = decl.get("risk_tier", "high")
        is_llm: bool = bool(decl.get("is_llm_or_agentic", False))

        blocking_article_ids: set[str] = set()
        for f in blocking_findings:
            for a in (f.get("eu_ai_act_articles") or [f.get("article", "")]):
                blocking_article_ids.add(str(a))

        articles_list: list[dict[str, Any]] = []
        for article, verdict in compliance_matrix.items():
            evidence_uris = [
                ref.get("uri", "") for ref in phase_artefacts.values()
                if isinstance(ref, dict) and ref.get("uri", "")
            ]
            supporting_tids = [
                tid for tid, crit in verifier_critiques.items()
                if article in (crit.get("article_citations") or [])
                and crit.get("verdict") in {"accept", "accept_with_notes"}
            ]
            source = _ARTICLE_PHASE.get(article, "ORCH")
            if source not in _VALID_PHASES:
                source = "ORCH"
            blocking_ids = [
                str(f.get("finding_id", f.get("control_id", "")))
                for f in blocking_findings
                if article in (f.get("eu_ai_act_articles") or [f.get("article", "")])
            ]
            articles_list.append({
                "article": article, "verdict": verdict,
                "evidence_uris": evidence_uris[:5],
                "supporting_template_ids": supporting_tids,
                "source_phase": source,
                "rationale": None,
                "cgsa_control_ids": [],
                "blocking_findings": blocking_ids,
            })

        final_verdict = decl.get("final_verdict") or "PASS_WITH_OBSERVATIONS"
        return {
            "engagement_id": engagement_id,
            "risk_tier": risk_tier if risk_tier != "prohibited" else "high",
            "is_llm_or_agentic": is_llm,
            "in_scope_articles": sorted(compliance_matrix.keys()),
            "articles": articles_list,
            "kpi_summary": {
                "intake_completeness_score": decl.get("intake_completeness_score"),
                "completeness_score": decl.get("completeness_score"),
                "regulatory_coverage_pct": decl.get("regulatory_coverage_pct"),
            },
            "blocking_findings_count": len(blocking_findings),
            "final_verdict": final_verdict,
            "generated_at": now,
        }

    # ------------------------------------------------------------------
    # T18 builder
    # ------------------------------------------------------------------

    def _build_t18(
        self,
        engagement_id: str,
        decl: dict,
        t17_ref: dict,
        now: str,
    ) -> dict[str, Any]:
        stage_a: dict = decl.get("stage_a") or {}
        phase_artefacts: dict[str, Any] = decl.get("phase_artefacts", {}) or {}
        ics = decl.get("intake_completeness_score")
        cs = decl.get("completeness_score")
        rc = decl.get("regulatory_coverage_pct")

        embedded = {
            tid: {"uri": ref.get("uri", ""), "sha256": ref.get("sha256", ""),
                  "template_id": tid}
            for tid, ref in phase_artefacts.items()
            if isinstance(ref, dict) and ref.get("uri") and "stub" not in ref.get("uri", "")
        }

        final_verdict = decl.get("final_verdict") or "PASS_WITH_OBSERVATIONS"
        n_blocking = len(decl.get("blocking_findings", []) or [])
        kpis_summary = (
            f"KPI0={ics:.2f}" if ics is not None else "KPI0=n/a",
            f"KPI1={cs:.2f}" if cs is not None else "KPI1=n/a",
            f"KPI2={rc:.1f}%" if rc is not None else "KPI2=n/a",
        )
        summary = (
            f"Autonomous AI audit complete for engagement {engagement_id}. "
            f"Final verdict: {final_verdict}. "
            f"{', '.join(kpis_summary)}. "
            f"Blocking findings: {n_blocking}. "
            f"See embedded artefacts T01a\u2013T17 for full evidence chain."
        )

        return {
            "engagement_id": engagement_id,
            "schema_version": "1.0.0",
            "engagement_metadata": {
                "provider_name": stage_a.get("provider_name", ""),
                "deployer_name": stage_a.get("deployer_name"),
                "system_name": stage_a.get("system_name", ""),
                "version": stage_a.get("version", "1.0"),
                "intended_purpose": stage_a.get("intended_purpose"),
                "modality": decl.get("modality", "tabular"),
                "risk_tier": decl.get("risk_tier", "high"),
                "deployment_context": decl.get("deployment_context", "b2b"),
                "is_llm_or_agentic": bool(decl.get("is_llm_or_agentic", False)),
                "annex_iii_sections": decl.get("annex_iii_sections", []),
            },
            "executive_summary": summary,
            "kpis": {
                "intake_completeness_score": ics,
                "completeness_score": cs,
                "regulatory_coverage_pct": rc,
                "kpi0_band": _kpi_band(ics),
                "kpi1_band": _kpi_band(cs),
                "kpi2_band": _kpi_band(rc, pct=True),
            },
            "final_verdict": final_verdict,
            "art43_decision": decl.get("art43_decision"),
            "embedded_artefacts": embedded,
            "compliance_matrix_ref": dict(t17_ref),
            "blocking_findings": decl.get("blocking_findings", []) or [],
            "positive_findings": decl.get("positive_findings", []) or [],
            "remediation_roadmap": decl.get("remediation_roadmap", []) or [],
            "cgsa_report_url": decl.get("cgsa_report_url"),
            "rendered_report": {"json_uri": ""},  # filled after report_render
            "hitl_required": bool(decl.get("hitl_required", False)),
            "hitl_reason": decl.get("hitl_reason"),
            "verifier_summary": decl.get("verifier_summary", {}),
            "generated_at": now,
        }
