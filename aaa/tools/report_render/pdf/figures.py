"""Embedded-figure drawing helper for the PDF renderer."""
from __future__ import annotations

from typing import Any


def _draw_figure(c: Any, cm: float, uri: str, caption: str, w_cm: int, h_cm: int,
                 y: float, height: float, margin: int, line_height: int) -> float:
    """Draw one embedded figure; return the new y cursor."""
    img_width, img_height = w_cm * cm, h_cm * cm
    if y - img_height < margin:
        c.showPage()
        c.setFont("Helvetica", 9)
        y = height - margin
    c.drawImage(uri, margin, y - img_height, width=img_width, height=img_height,
                preserveAspectRatio=True, mask="auto")
    y -= img_height + line_height
    c.drawString(margin, y, caption)
    return y - line_height * 2
