"""Best-effort PDF rendering of the report text body via reportlab."""
from __future__ import annotations

import logging
import os
from typing import Optional

from aaa.tools.report_render.pdf.figures import _draw_figure

logger = logging.getLogger(__name__)

#: line-start trigger → (uri key, caption, width_cm, height_cm)
_FIGURES = {
    "Final verdict": ("risk_heatmap", "Figure 1: Risk Assessment Matrix", 14, 10),
    "Compliance matrix": ("maturity_radar", "Figure 2: AI Governance Maturity by Domain", 12, 10),
}


def _try_reportlab(text_body: str, risk_heatmap_uri: str | None = None,
                   maturity_radar_uri: str | None = None) -> Optional[bytes]:
    """Render the text body into a simple A4 PDF. Returns ``None`` on failure."""
    try:
        from io import BytesIO

        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.units import cm  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
    except ImportError:
        return None
    try:
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        _width, height = A4
        margin, line_height = 40, 11
        y = height - margin
        c.setFont("Helvetica", 9)
        uris = {"risk_heatmap": risk_heatmap_uri, "maturity_radar": maturity_radar_uri}
        drawn: set[str] = set()
        for raw_line in text_body.splitlines():
            if y < margin:
                c.showPage()
                c.setFont("Helvetica", 9)
                y = height - margin
            c.drawString(margin, y, raw_line[:120])
            y -= line_height
            for trigger, (key, caption, w_cm, h_cm) in _FIGURES.items():
                uri = uris.get(key)
                if (key not in drawn and raw_line.startswith(trigger)
                        and uri and os.path.exists(uri)):
                    y = _draw_figure(c, cm, uri, caption, w_cm, h_cm,
                                     y, height, margin, line_height)
                    drawn.add(key)
        c.save()
        return buf.getvalue()
    except Exception as exc:  # pragma: no cover
        logger.warning("reportlab render failed: %s; falling back to text.", exc)
        return None
