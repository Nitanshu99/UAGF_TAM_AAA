"""Assembles the customer-facing conformity report PDF (reportlab platypus).

Layered like the results page: cover (verdict + KPIs) → executive summary and
risk classification → article matrix → findings → governance → evidence →
documentation inventory. Every section tolerates missing data, so the same
builder serves live pipeline runs and the batch CLI over persisted JSONs.
"""
from __future__ import annotations

import io
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from aaa.tools.report_render.pdf.cover import build_cover
from aaa.tools.report_render.pdf.dossier import build_dossier
from aaa.tools.report_render.pdf.evidence import build_evidence
from aaa.tools.report_render.pdf.findings import build_findings
from aaa.tools.report_render.pdf.governance import build_governance
from aaa.tools.report_render.pdf.images import fetch_image
from aaa.tools.report_render.pdf.matrix import build_matrix
from aaa.tools.report_render.pdf.summary import build_summary
from aaa.tools.report_render.pdf.theme import MUTED


def _footer(canvas: Any, _doc: Any) -> None:
    """Draw the confidentiality footer and page number on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.6 * cm, 1.0 * cm,
                      "Confidential — EU AI Act conformity assessment report")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def build_pdf(t18: dict[str, Any], t17: dict[str, Any] | None = None,
              audit_state: dict[str, Any] | None = None, store: Any = None) -> bytes:
    """Render the full report and return the PDF bytes.

    :param t18: The T18 audit-report payload (required).
    :type t18: dict[str, Any]
    :param t17: The T17 compliance-matrix payload.
    :type t17: dict[str, Any] | None
    :param audit_state: The audit state (risk classification, CGSA, evidence).
    :type audit_state: dict[str, Any] | None
    :param store: Evidence store for figure resolution; ``None`` skips figures.
    :type store: Any
    :returns: The rendered PDF document.
    :rtype: bytes
    """
    t17, state = t17 or {}, audit_state or {}
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.6 * cm,
                            rightMargin=1.6 * cm, topMargin=1.4 * cm,
                            bottomMargin=1.6 * cm, title=t18.get("engagement_id", ""))
    story: list[Any] = build_cover(t18, t17)
    heatmap = fetch_image(t18.get("risk_heatmap_uri"), store, 13, 9.5)
    if heatmap is not None:
        story += [Spacer(1, 6), heatmap]
    story.append(PageBreak())
    story += build_summary(t18, state)
    story += build_matrix(t17)
    story += build_findings(t18)
    story += build_governance(state, t18, store)
    story += build_evidence(state, store)
    story += build_dossier(state)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
