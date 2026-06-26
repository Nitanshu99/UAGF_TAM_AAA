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

Phase 6 uses a prompt-driven synthesis path in normal mode and falls back to
deterministic assembly in offline / CI mode.
"""
from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.platform.evidence import EvidenceStore
from aaa.tools.template_render import template_render
from aaa.tools.report_render import report_render
from aaa.tools.maturity_radar_render import maturity_radar_render
from aaa.tools.risk_heatmap_render import risk_heatmap_render

logger = logging.getLogger(__name__)
_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_PROMPT_NAME = "phase6_report"

# Article → source phase mapping (used to populate T17.articles.source_phase)
_ARTICLE_PHASE: dict[str, str] = {
    "Art.5": "P1", "Art.6": "P1", "Art.9": "P5", "Art.10": "P2",
    "Art.11": "P1", "Art.12": "P5", "Art.13": "P1", "Art.14": "P3",
    "Art.15": "P3", "Art.17": "P5", "Art.43": "P1", "Art.50": "P4",
    "Art.72": "P5", "Annex_III": "P1",
    "Annex_IV": "P1", "GPAI_51": "L", "GPAI_52": "L", "GPAI_53": "L",
    "GPAI_54": "L", "GPAI_55": "L", "Annex_XI": "L", "Annex_XII": "L",
}
_VALID_PHASES = {"P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIV", "ORCH"}

_KPI_BANDS = [
    (0.90, "PASS"),
    (0.75, "PASS_WITH_OBSERVATIONS"),
    (0.0,  "FAIL"),
]

_METHODOLOGY_BASIS = (
    "This conformity assessment was conducted in accordance with the UAGF-TAM audit "
    "protocol (v1.0.0), applying the methodology of ISAE 3000 (Revised) for "
    "non-financial assurance engagements and ISO 19011:2018 for audit programme "
    "management. The audit was performed by an automated multi-agent system; results "
    "should be reviewed by a qualified human auditor before regulatory submission "
    "under Article 43 of the EU AI Act."
)


def _kpi_band(value: float | None, pct: bool = False) -> str | None:
    if value is None:
        return None
    v = value if not pct else value / 100.0
    for threshold, band in _KPI_BANDS:
        if v >= threshold:
            return band
    return "FAIL"


def _management_response_shell(
    findings: list[dict[str, Any]],
    remediation: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Generate client-fill management-response rows for material findings."""
    by_control = {str(item.get("control_id", "")): item for item in remediation}
    shell: list[dict[str, str]] = []
    for idx, finding in enumerate(findings, start=1):
        materiality = finding.get("materiality")
        if materiality not in {"material", "possibly_material"}:
            continue
        finding_id = finding.get("finding_id") or f"F-{idx:03d}"
        control_id = str(finding.get("control_id", ""))
        remediation_item = by_control.get(control_id, {})
        recommendation = (
            finding.get("recommendation")
            or finding.get("recommended_action")
            or remediation_item.get("recommended_action")
            or remediation_item.get("gap_detail")
            or finding.get("gap_detail")
            or ""
        )
        owner = (
            finding.get("assigned_owner")
            or remediation_item.get("assigned_owner")
            or "[To be assigned]"
        )
        shell.append({
            "finding_id": str(finding_id),
            "finding_summary": str(finding.get("description", ""))[:200],
            "materiality": str(materiality),
            "auditor_recommendation": str(recommendation),
            "management_response": "[Management response pending]",
            "action_plan": "[Action plan pending]",
            "target_completion_date": "[Date pending]",
            "responsible_owner": str(owner),
        })
    return shell


def _auditor_opinion(decl: dict[str, Any], final_verdict: str) -> dict[str, str]:
    """Build a deterministic ISAE 3000-style opinion block."""
    material_count = int(decl.get("material_findings_count", 0) or 0)
    findings = decl.get("blocking_findings", []) or []
    material_ids = [
        str(f.get("finding_id", f.get("control_id", "finding")))
        for f in findings
        if f.get("materiality") in {"material", "possibly_material"}
    ]
    observations = [
        f for f in findings if f.get("materiality") in {"possibly_material", "observation"}
    ]
    obs_summary = "; ".join(
        f"{f.get('finding_id', 'finding')}: {f.get('description', '')}" for f in observations[:5]
    )
    insufficient_articles = sorted(
        a for a, v in (decl.get("compliance_matrix", {}) or {}).items()
        if v == "INSUFFICIENT_EVIDENCE"
    )

    # FAIL (confirmed non-conformity) → adverse; unverifiable mandatory requirement
    # → disclaimer; otherwise unqualified / qualified by findings.
    if decl.get("hitl_required") and not final_verdict:
        opinion_type = "disclaimer_of_opinion"
    elif final_verdict == "FAIL":
        opinion_type = "adverse"
    elif decl.get("opinion_disclaimer"):
        opinion_type = "disclaimer_of_opinion"
    elif final_verdict == "PASS" and material_count == 0 and not material_ids:
        opinion_type = "unqualified"
    else:
        opinion_type = "qualified"

    system_name = (decl.get("stage_a") or {}).get("system_name") or "the AI system"
    if opinion_type == "unqualified":
        opinion = (
            f"In our opinion, based on the procedures performed, {system_name} was, "
            "in all material respects, designed and documented in conformity with the "
            "applicable EU AI Act requirements assessed by UAGF-TAM."
        )
        basis = "No material findings were identified from independently verified evidence."
    elif opinion_type == "qualified":
        opinion = (
            f"Except for the matters described in the Basis for Conclusion, {system_name} "
            "was designed and documented in conformity with the applicable EU AI Act "
            "requirements assessed by UAGF-TAM."
        )
        basis = (
            "Qualified matters: "
            f"{obs_summary or (', '.join(material_ids) if material_ids else 'see findings register')}."
        )
    elif opinion_type == "adverse":
        opinion = (
            f"In our opinion, due to the significance of the matters described in the "
            f"Basis for Conclusion, {system_name} is not in conformity with the applicable "
            "EU AI Act requirements assessed by UAGF-TAM."
        )
        fail_articles = sorted(
            a for a, v in (decl.get("compliance_matrix", {}) or {}).items() if v == "FAIL"
        )
        basis = (
            "The final audit verdict is FAIL. Confirmed non-conformities on: "
            f"{', '.join(fail_articles) or 'see findings register'}."
        )
    else:
        opinion = (
            f"We do not express an assurance conclusion on {system_name} because sufficient "
            "appropriate evidence was not available to verify mandatory high-risk requirements."
        )
        basis = (
            "Independent verification could not be performed for: "
            f"{', '.join(insufficient_articles) or 'core high-risk requirements'}. "
            + str(decl.get("hitl_reason") or "")
        ).strip()

    scope = (
        "The assessment covered admitted intake artefacts, phase reports, verifier "
        "critiques, the T17 compliance matrix, and CGSA handoff evidence available to "
        "UAGF-TAM at report generation time. It did not extend beyond evidence admitted "
        "to the audit evidence store."
    )
    return {
        "opinion_type": opinion_type,
        "opinion_paragraph": opinion,
        "basis_paragraph": basis,
        "methodology_basis": _METHODOLOGY_BASIS,
        "scope_paragraph": scope,
    }


class ReportArchitect(BaseAgent):
    """Phase 6 — Report Architect."""

    def __init__(
        self,
        evidence_store: EvidenceStore,
        model: str | None = None,
        service_tier: str | None = None,
    ):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="ReportArchitect",
            model=resolve_model("ReportArchitect", model),
            service_tier=resolve_service_tier("ReportArchitect", service_tier),
        )
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
        heatmap_tmp = os.path.join(tempfile.gettempdir(), f"heatmap_{engagement_id}.png")
        try:
            local = risk_heatmap_render(
                findings=t18.get("blocking_findings", []),
                output_path=heatmap_tmp,
            )
            t18["risk_heatmap_uri"] = self._persist_png(engagement_id, local, "risk_heatmap")
        except Exception as exc:
            logger.warning("risk_heatmap_render failed (%s); continuing without heatmap.", exc)
            t18["risk_heatmap_uri"] = None
        radar_tmp = os.path.join(tempfile.gettempdir(), f"radar_{engagement_id}.png")
        domain_scores = decl.get("cgsa_domain_scores", {}) or {}
        try:
            local_radar = maturity_radar_render(domain_scores, radar_tmp) if domain_scores else None
            t18["maturity_radar_uri"] = (
                self._persist_png(engagement_id, local_radar, "maturity_radar") if local_radar else None
            )
        except Exception as exc:
            logger.warning("maturity_radar_render failed (%s); continuing without radar.", exc)
            t18["maturity_radar_uri"] = None
        llm_fallback_mode = _OFFLINE
        llm_summary: str | None = None
        if not _OFFLINE:
            try:
                llm_payload = await self.acompletion_json(
                    _PROMPT_NAME,
                    {
                        "task": message.get("task_brief")
                        or "Compose the final T18 audit report from admitted artefacts.",
                        "evidence_uris": message.get("evidence_uris", []),
                        "declaration_summary": decl,
                        "t17_payload": t17,
                        "t18_seed": t18,
                    },
                )
                llm_summary = (
                    llm_payload.get("executive_summary")
                    or llm_payload.get("summary")
                    or llm_payload.get("rationale_summary")
                )
                if isinstance(llm_payload.get("auditor_opinion"), dict):
                    t18["auditor_opinion"].update(llm_payload["auditor_opinion"])
                llm_fallback_mode = False
            except Exception as exc:
                logger.warning("ReportArchitect prompt runtime failed (%s); using deterministic fallback.", exc)
        prompt_note = self.prompt_note(_PROMPT_NAME, llm_fallback_mode)
        t18["executive_summary"] = f"{llm_summary or t18['executive_summary']} {prompt_note}".strip()

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
                llm_summary
                or
                f"Phase 6 complete. final_verdict={final_verdict}, "
                f"articles={len(t17.get('articles', []))}, "
                f"renderer={rendered.get('renderer')}."
            ),
            confidence=0.95,
            tool_calls=[
                {"tool": "template_render", "result": f"T17 uri={t17_ref['uri']}"},
                {"tool": "report_render", "result": f"renderer={rendered.get('renderer')}"},
                {"tool": "template_render", "result": f"T18 uri={t18_ref['uri']}"},
                {"tool": "prompt_runtime", "result": prompt_note},
            ],
            declaration_verification_delta={
                "phase_artefacts": {
                    "T17_compliance_matrix": dict(t17_ref),
                    "T18_audit_report": dict(t18_ref),
                },
                "final_verdict": final_verdict,
                "auditor_opinion": t18.get("auditor_opinion"),
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _persist_png(self, engagement_id: str, local_path: str | None, kind: str) -> str | None:
        """Persist a rendered PNG to the evidence store; return a stable URI.

        The renderers write to a temp path that vanishes on reboot. We store the
        bytes so the report is durable and reviewable offline, falling back to the
        local path only if persistence fails.
        """
        if not local_path or not os.path.exists(local_path):
            return local_path
        try:
            with open(local_path, "rb") as handle:
                data = handle.read()
            return self.store.store_file(
                engagement_id=engagement_id,
                phase="phase_6",
                artefact_type=kind,
                filename=f"{kind}.png",
                content_type="image/png",
                data=data,
                agent_name=self.name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist %s PNG (%s); using local path.", kind, exc)
            return local_path

    # ------------------------------------------------------------------
    # T17 builder
    # ------------------------------------------------------------------

    def _build_t17(self, engagement_id: str, decl: dict, now: str) -> dict[str, Any]:
        compliance_matrix: dict[str, str] = decl.get("compliance_matrix", {}) or {}
        blocking_findings: list[dict] = decl.get("blocking_findings", []) or []
        article_evidence: dict[str, Any] = decl.get("article_evidence", {}) or {}
        risk_tier: str = decl.get("risk_tier", "high")
        is_llm: bool = bool(decl.get("is_llm_or_agentic", False))

        articles_list: list[dict[str, Any]] = []
        for article, verdict in compliance_matrix.items():
            ev = article_evidence.get(article, {}) or {}
            source = _ARTICLE_PHASE.get(article, "ORCH")
            if source not in _VALID_PHASES:
                source = "ORCH"
            articles_list.append({
                "article": article,
                "verdict": verdict,
                "evidence_uris": (ev.get("evidence_uris") or [])[:5],
                "supporting_template_ids": ev.get("supporting_template_ids", []),
                "source_phase": source,
                "rationale": ev.get("rationale"),
                "cgsa_control_ids": ev.get("cgsa_control_ids", []),
                "blocking_findings": ev.get("finding_ids", []),
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
        blocking_findings = decl.get("blocking_findings", []) or []
        positive_findings = decl.get("positive_findings", []) or []
        remediation_roadmap = decl.get("remediation_roadmap", []) or []
        management_response = _management_response_shell(
            blocking_findings + positive_findings,
            remediation_roadmap,
        )
        auditor_opinion = _auditor_opinion(decl, final_verdict)

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
            "auditor_opinion": auditor_opinion,
            "art43_decision": decl.get("art43_decision"),
            "embedded_artefacts": embedded,
            "compliance_matrix_ref": dict(t17_ref),
            "blocking_findings": blocking_findings,
            "positive_findings": positive_findings,
            "remediation_roadmap": remediation_roadmap,
            "management_response": management_response,
            "risk_heatmap_uri": None,
            "maturity_radar_uri": None,
            "cgsa_report_url": decl.get("cgsa_report_url"),
            "rendered_report": {"json_uri": ""},  # filled after report_render
            "hitl_required": bool(decl.get("hitl_required", False)),
            "hitl_reason": decl.get("hitl_reason"),
            "verifier_summary": decl.get("verifier_summary", {}),
            "generated_at": now,
        }
