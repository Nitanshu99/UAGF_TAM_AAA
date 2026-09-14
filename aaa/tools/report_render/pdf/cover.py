"""Cover page of the customer-facing PDF: banner, system identity, verdict, KPIs."""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from aaa.tools.report_render.pdf.status import build_status, verdict_label
from aaa.tools.report_render.pdf.tables import badge, kv_table
from aaa.tools.report_render.pdf.theme import INK, STYLES, verdict_color


def _banner(t18: dict[str, Any], t17: dict[str, Any]) -> Table:
    """Build the classification banner line (id · date · risk tier)."""
    tier = (t17.get("risk_tier") or "").upper() or "UNSPECIFIED"
    text = (f"{t18.get('engagement_id', '')} · {t18.get('generated_at', '')[:16]} UTC · "
            f"{tier} RISK · EU AI Act conformity assessment")
    row = Table([[Paragraph(text, STYLES["banner"])]], colWidths=[16.5 * cm])
    row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return row


def kpi_text(kpis: dict[str, Any], key: str, band: str,
             spec: str = ".2f", unit: str = "") -> str:
    """Format one cover KPI with its band; an absent KPI is "not measured".

    A ``0`` default here printed ``0.00`` for a KPI the run never computed, and
    a ``None`` value raised in the format spec (T-095).

    :param kpis: The T18 ``kpis`` block.
    :param key: KPI field name.
    :param band: The field holding that KPI's band.
    :param spec: Format spec for the value.
    :param unit: Suffix after the value.
    :returns: Cover-table text.
    """
    value = kpis.get(key)
    if value is None:
        return "not measured"
    return f"{float(value):{spec}}{unit}  ({kpis.get(band) or '—'})"


def build_cover(t18: dict[str, Any], t17: dict[str, Any]) -> list[Any]:
    """Build the cover flowables from the T18/T17 payloads.

    :param t18: The T18 audit-report payload.
    :type t18: dict[str, Any]
    :param t17: The T17 compliance-matrix payload (may be empty).
    :type t17: dict[str, Any]
    :returns: Cover-page flowables.
    :rtype: list[Any]
    """
    meta = t18.get("engagement_metadata") or {}
    kpis = t18.get("kpis") or {}
    verdict = (t18.get("final_verdict") or "UNKNOWN").upper()
    flow: list[Any] = [_banner(t18, t17), Spacer(1, 18)]
    system = f"{meta.get('system_name', 'AI system')} v{meta.get('version', '')}".strip(" v")
    flow.append(Paragraph(system, STYLES["title"]))
    flow.append(Paragraph(meta.get("provider_name", ""), STYLES["subtitle"]))
    flow.append(Spacer(1, 10))
    # Q12: "FINAL VERDICT" on an unsigned, review-pending report is a claim the
    # runtime had already declined to make. The banner follows the signature.
    flow.append(badge(verdict_label(t18), verdict_color(verdict)))
    flow += build_status(t18)
    flow.append(Spacer(1, 14))
    flow.append(kv_table([
        ("Provider", meta.get("provider_name") or "—"),
        ("Deployer", meta.get("deployer_name") or "—"),
        ("Intended purpose", meta.get("intended_purpose") or "—"),
        ("Intake completeness", kpi_text(kpis, "intake_completeness_score", "kpi0_band")),
        ("Evidence completeness", kpi_text(kpis, "completeness_score", "kpi1_band")),
        ("Regulatory coverage", kpi_text(kpis, "regulatory_coverage_pct", "kpi2_band",
                                         ".1f", "%")),
    ]))
    flow.append(Spacer(1, 10))
    return flow
