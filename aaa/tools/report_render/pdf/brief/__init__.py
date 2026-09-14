"""Render the Agent 14 client brief (Markdown) as a customer-facing PDF.

The brief is the only deliverable in the customer folder written to be read
without an auditor beside you, and it was the only one with no PDF: the wizard
offered the formal report as a PDF and the brief not at all, so the document
most likely to be forwarded to a non-specialist was the one that never left the
page. This renders it with the same palette and page furniture as
``pdf.builder``, so the two read as one product.

Only the constructs the brief actually emits are handled — ATX headings,
blockquote, ``-`` bullets, pipe tables, and the ``**bold**`` / `` `code` ``
inline spans. Anything else falls through to a paragraph rather than being
dropped, which keeps an unrecognised line visible to the reader instead of
silently missing from their copy.
"""
from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from aaa.tools.report_render.pdf.brief.flowables import markdown_flowables
from aaa.tools.report_render.pdf.brief.page import footer


def build_brief_pdf(markdown: str, engagement_id: str = "") -> bytes:
    """Render the client brief Markdown as PDF bytes.

    :param markdown: The client brief as written by the ClientBrief agent.
    :param engagement_id: Engagement identifier used in the PDF title.
    :returns: The PDF document.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.6 * cm,
        title=f"{engagement_id} client brief".strip())
    doc.build(markdown_flowables(markdown), onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


__all__ = ["build_brief_pdf", "markdown_flowables"]
