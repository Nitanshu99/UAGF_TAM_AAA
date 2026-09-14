"""Colour palette and paragraph styles for the customer-facing PDF report.

Mirrors the Streamlit UI design language (slate neutrals + Bootstrap accent
colours) so the on-screen results page and the downloadable report read as
one product.
"""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
BORDER = colors.HexColor("#e2e8f0")
SURFACE = colors.HexColor("#f8fafc")
GREEN = colors.HexColor("#198754")
AMBER = colors.HexColor("#b45309")
RED = colors.HexColor("#dc3545")
INFO = colors.HexColor("#0c7c95")

VERDICT_COLORS = {"PASS": GREEN, "PASS_WITH_OBSERVATIONS": AMBER, "FAIL": RED,
                  # No opinion expressed: deliberately neutral, and mapped
                  # explicitly so it is not the "unknown verdict" fallback.
                  "DISCLAIMER_OF_OPINION": MUTED}
SEVERITY_COLORS = {"material": RED, "possibly_material": AMBER, "observation": INFO}
SEVERITY_ORDER = ("material", "possibly_material", "observation")

STYLES: dict[str, ParagraphStyle] = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=24,
                            leading=29, textColor=INK),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=12,
                               leading=16, textColor=MUTED),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15,
                         leading=19, textColor=INK, spaceBefore=14, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5,
                         leading=15, textColor=INK, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5,
                           leading=13.5, textColor=INK),
    "muted": ParagraphStyle("muted", fontName="Helvetica", fontSize=8.5,
                            leading=12, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5,
                           leading=11.5, textColor=INK),
    "banner": ParagraphStyle("banner", fontName="Helvetica-Bold", fontSize=8.5,
                             leading=11, textColor=colors.white),
}


def verdict_color(verdict: str | None) -> colors.Color:
    """Return the accent colour for *verdict* (muted slate when unknown).

    :param verdict: PASS / PASS_WITH_OBSERVATIONS / FAIL /
        DISCLAIMER_OF_OPINION, or ``None``.
    :type verdict: str | None
    :returns: The mapped colour.
    :rtype: colors.Color
    """
    return VERDICT_COLORS.get((verdict or "").upper(), MUTED)
