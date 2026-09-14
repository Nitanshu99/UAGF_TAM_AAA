"""report_render — stitch admitted T01a–T17 artefacts into the final report.

Produces the Phase 6 deliverable (PDF + machine-readable JSON), persists
both to the Evidence Store, and returns the rendered metadata block to be
embedded in T18 (§4.5).  The renderer is reportlab when available, otherwise
a plain-text/UTF-8 fallback so the function never raises when reportlab is
missing.  The JSON copy is always produced — it is the machine-readable
contract — while the PDF is best-effort.
"""
from __future__ import annotations

from aaa.tools.report_render.core import report_render
from aaa.tools.report_render.pdf.legacy import _try_reportlab  # noqa: F401 (test access)
from aaa.tools.report_render.text.body import _build_text_body  # noqa: F401 (test access)

__all__ = ["report_render"]
