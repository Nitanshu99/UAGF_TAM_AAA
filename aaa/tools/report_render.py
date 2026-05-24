"""
report_render — stitch admitted T01a–T17 artefacts into the final Phase 6
report (PDF + machine-readable JSON), persist both to the Evidence Store,
return the rendered metadata block to be embedded in T18 (§4.5).

  report_render(t18_payload, *, engagement_id, store, agent_name)
    -> {pdf_uri, pdf_bytes_size, json_uri, renderer}

The renderer is reportlab when available, otherwise a plain-text/UTF-8
fallback so the function never raises in offline mode.  The JSON copy is
always produced — it is the machine-readable contract — while the PDF is
best-effort.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from aaa.platform.evidence import EvidenceStore

logger = logging.getLogger(__name__)


def _build_text_body(t18: dict[str, Any]) -> str:
    """Plain-text rendering used when reportlab is unavailable."""
    md = t18.get("engagement_metadata", {}) or {}
    kpis = t18.get("kpis", {}) or {}
    lines: list[str] = [
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
        "Executive summary",
        "-" * 70,
        t18.get("executive_summary", "") or "",
        "",
        "Final verdict    : " + str(t18.get("final_verdict", "")),
        "",
        "KPIs (§9.1)",
        "-" * 70,
        f"KPI 0 intake_completeness_score : {kpis.get('intake_completeness_score')}"
        f"  band={kpis.get('kpi0_band')}",
        f"KPI 1 completeness_score        : {kpis.get('completeness_score')}"
        f"  band={kpis.get('kpi1_band')}",
        f"KPI 2 regulatory_coverage_pct   : {kpis.get('regulatory_coverage_pct')}"
        f"  band={kpis.get('kpi2_band')}",
        "",
    ]

    art43 = t18.get("art43_decision") or {}
    if art43:
        lines += [
            "Article 43 — Conformity assessment procedure",
            "-" * 70,
            f"Procedure : {art43.get('procedure', '')}",
            f"Rationale : {art43.get('rationale', '')}",
            "",
        ]

    matrix_ref = t18.get("compliance_matrix_ref") or {}
    lines += [
        "Compliance matrix (T17)",
        "-" * 70,
        f"URI       : {matrix_ref.get('uri', '')}",
        f"SHA-256   : {matrix_ref.get('sha256', '')}",
        "",
    ]

    embedded = t18.get("embedded_artefacts", {}) or {}
    lines += ["Embedded artefacts (T01a–T16)", "-" * 70]
    for tid in sorted(embedded.keys()):
        ref = embedded[tid] or {}
        lines.append(f"  {tid:36s} → {ref.get('uri', '')}")
    lines.append("")

    blocking = t18.get("blocking_findings", []) or []
    if blocking:
        lines += ["Blocking findings", "-" * 70]
        for f in blocking:
            lines.append(
                f"  [{f.get('severity', 'major'):>10s}] "
                f"{f.get('article', '')} · {f.get('description', '')}"
            )
        lines.append("")

    roadmap = t18.get("remediation_roadmap", []) or []
    if roadmap:
        lines += ["Remediation roadmap", "-" * 70]
        for item in roadmap:
            lines.append(
                f"  #{item.get('rank', 0):02d} {item.get('control_id', ''):8s} "
                f"[{item.get('gap_severity', '')}] {item.get('action', item.get('recommended_action', ''))}"
            )
        lines.append("")

    cgsa_url = t18.get("cgsa_report_url")
    if cgsa_url:
        lines += [f"Full CGSA governance report: {cgsa_url}", ""]

    lines += [
        "-" * 70,
        f"Generated at : {t18.get('generated_at', '')}",
        "End of report.",
    ]
    return "\n".join(lines)


def _try_reportlab(text_body: str) -> Optional[bytes]:
    """Render the text body into a simple A4 PDF via reportlab. Returns None on failure."""
    try:
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
        from io import BytesIO
    except ImportError:
        return None
    try:
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        margin = 40
        line_height = 11
        y = height - margin
        c.setFont("Helvetica", 9)
        for raw_line in text_body.splitlines():
            if y < margin:
                c.showPage()
                c.setFont("Helvetica", 9)
                y = height - margin
            c.drawString(margin, y, raw_line[:120])
            y -= line_height
        c.save()
        return buf.getvalue()
    except Exception as exc:  # pragma: no cover
        logger.warning("reportlab render failed: %s; falling back to text.", exc)
        return None


def report_render(
    t18_payload: dict[str, Any],
    *,
    engagement_id: str,
    store: EvidenceStore,
    agent_name: str,
) -> dict[str, Any]:
    """Render T18 to PDF + JSON, persist both, return rendering metadata."""
    text_body = _build_text_body(t18_payload)
    pdf_bytes = _try_reportlab(text_body)

    json_uri = store.store_artefact(
        engagement_id=engagement_id,
        phase="phase_6",
        artefact_type="T18_audit_report.json",
        content=t18_payload,
        agent_name=agent_name,
    )

    if pdf_bytes is not None:
        pdf_payload = {
            "format": "pdf",
            "encoding": "latin-1",
            "body": pdf_bytes.decode("latin-1"),
            "bytes_size": len(pdf_bytes),
        }
        pdf_uri = store.store_artefact(
            engagement_id=engagement_id,
            phase="phase_6",
            artefact_type="T18_audit_report.pdf",
            content=pdf_payload,
            agent_name=agent_name,
        )
        return {
            "pdf_uri": pdf_uri,
            "pdf_bytes_size": len(pdf_bytes),
            "json_uri": json_uri,
            "renderer": "reportlab",
        }

    text_uri = store.store_artefact(
        engagement_id=engagement_id,
        phase="phase_6",
        artefact_type="T18_audit_report.txt",
        content={"format": "text", "body": text_body, "bytes_size": len(text_body)},
        agent_name=agent_name,
    )
    return {
        "pdf_uri": text_uri,
        "pdf_bytes_size": len(text_body.encode("utf-8")),
        "json_uri": json_uri,
        "renderer": "text_fallback",
    }
