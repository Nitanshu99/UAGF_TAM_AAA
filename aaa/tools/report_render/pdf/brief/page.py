"""Page furniture for the client-brief PDF: the footer drawn on every page."""
from __future__ import annotations

from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from aaa.tools.report_render.pdf.theme import MUTED


def footer(canvas: Any, _doc: Any) -> None:
    """Draw the plain-language footer and page number on every page.

    :param canvas: ReportLab canvas the page is being drawn on.
    :param _doc: The document template (unused, required by ReportLab).
    """
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.6 * cm, 1.0 * cm,
                      "Plain-language summary — the formal audit report governs")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


__all__ = ["footer"]
