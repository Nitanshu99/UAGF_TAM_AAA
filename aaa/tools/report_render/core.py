"""Render T18 to PDF + JSON, persist both, return rendering metadata."""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.evidence import EvidenceStore
from aaa.tools.report_render.pdf.legacy import _try_reportlab
from aaa.tools.report_render.text.body import _build_text_body

logger = logging.getLogger(__name__)


def report_render(t18_payload: dict[str, Any], *, engagement_id: str,
                  store: EvidenceStore, agent_name: str,
                  t17_payload: dict[str, Any] | None = None,
                  audit_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Render T18 to PDF (best-effort) + JSON (always) and persist both.

    :param t18_payload: The T18 audit-report payload.
    :param engagement_id: Engagement identifier.
    :param store: Evidence store for the rendered artefacts.
    :param agent_name: Producing agent (provenance).
    :param t17_payload: T17 compliance matrix (drives the article table).
    :param audit_state: Audit state (risk classification, CGSA, evidence).
    :returns: ``{pdf_uri, pdf_bytes_size, json_uri, renderer}``.
    """
    try:
        from aaa.tools.report_render.pdf.builder import build_pdf
        pdf_bytes: bytes | None = build_pdf(t18_payload, t17_payload, audit_state, store)
    except Exception as exc:  # noqa: BLE001 — rendering must never break Phase 6
        logger.warning("platypus report build failed (%s); using legacy renderer.", exc)
        pdf_bytes = _try_reportlab(
            _build_text_body(t18_payload),
            t18_payload.get("risk_heatmap_uri"),
            t18_payload.get("maturity_radar_uri"),
        )
    json_uri = store.store_artefact(
        engagement_id=engagement_id, phase="phase_6",
        artefact_type="T18_audit_report.json", content=t18_payload, agent_name=agent_name)

    if pdf_bytes is not None:
        pdf_payload = {
            "format": "pdf", "encoding": "latin-1",
            "body": pdf_bytes.decode("latin-1"), "bytes_size": len(pdf_bytes),
        }
        pdf_uri = store.store_artefact(
            engagement_id=engagement_id, phase="phase_6",
            artefact_type="T18_audit_report.pdf", content=pdf_payload, agent_name=agent_name)
        return {"pdf_uri": pdf_uri, "pdf_bytes_size": len(pdf_bytes),
                "json_uri": json_uri, "renderer": "reportlab"}

    text_body = _build_text_body(t18_payload)
    text_uri = store.store_artefact(
        engagement_id=engagement_id, phase="phase_6",
        artefact_type="T18_audit_report.txt",
        content={"format": "text", "body": text_body, "bytes_size": len(text_body)},
        agent_name=agent_name)
    return {"pdf_uri": text_uri, "pdf_bytes_size": len(text_body.encode("utf-8")),
            "json_uri": json_uri, "renderer": "text_fallback"}
