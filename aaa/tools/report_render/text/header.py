"""Header, opinion, and KPI sections of the plain-text report body."""
from __future__ import annotations

from typing import Any


def header_lines(t18: dict[str, Any]) -> list[str]:
    """Render the report banner and engagement metadata block."""
    md = t18.get("engagement_metadata", {}) or {}
    return [
        "UAGF-TAM — Autonomous AI Auditor — Conformity Assessment Report",
        "=" * 70,
        f"Engagement ID    : {t18.get('engagement_id', '')}",
        f"Schema version   : {t18.get('schema_version', '')}",
        f"Provider         : {md.get('provider_name', '')}",
        f"System           : {md.get('system_name', '')} v{md.get('version', '')}",
        f"Modality / tier  : {md.get('modality', '')} / {md.get('risk_tier', '')}",
        f"Deployment       : {md.get('deployment_context', '')}",
        f"Annex III §§     : {', '.join(md.get('annex_iii_sections', []) or []) or '—'}",
        "",
    ]


def opinion_lines(t18: dict[str, Any]) -> list[str]:
    """Render the independent assurance conclusion section (may be empty)."""
    opinion = t18.get("auditor_opinion") or {}
    if not opinion:
        return []
    lines = [
        "Independent Assurance Conclusion",
        "-" * 70,
        f"Opinion type : {opinion.get('opinion_type', '')}",
        opinion.get("opinion_paragraph", "") or "",
    ]
    if opinion.get("opinion_type") in {"qualified", "adverse"}:
        lines += ["Basis for Conclusion", "-" * 70, opinion.get("basis_paragraph", "") or ""]
    lines += [opinion.get("methodology_basis", "") or "",
              opinion.get("scope_paragraph", "") or "", ""]
    return lines


def summary_kpi_lines(t18: dict[str, Any]) -> list[str]:
    """Render the executive summary, final verdict, and KPI block."""
    kpis = t18.get("kpis", {}) or {}
    return [
        "Executive summary", "-" * 70,
        t18.get("executive_summary", "") or "", "",
        "Final verdict    : " + str(t18.get("final_verdict", "")), "",
        "KPIs (§9.1)", "-" * 70,
        f"KPI 0 intake_completeness_score : {kpis.get('intake_completeness_score')}"
        f"  band={kpis.get('kpi0_band')}",
        f"KPI 1 completeness_score        : {kpis.get('completeness_score')}"
        f"  band={kpis.get('kpi1_band')}",
        f"KPI 2 regulatory_coverage_pct   : {kpis.get('regulatory_coverage_pct')}"
        f"  band={kpis.get('kpi2_band')}",
        "",
    ]
