"""One document row of the evidence table, and how a measured value is rendered."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph

from aaa.tools.report_render.pdf.tables import kv_table
from aaa.tools.report_render.pdf.theme import STYLES

_SKIP_KEYS = {"evidence_source", "articles", "error"}
def _document(evidence: dict[str, Any]) -> list[Any]:
    """Render one evidence document as reference rows / scalar values."""
    if evidence.get("evidence_source") == "not_required":
        return [Paragraph(f"Not required for this engagement — {evidence.get('reason', '')}.",
                          STYLES["muted"])]
    if evidence.get("error"):
        return [Paragraph("Evidence for this section could not be collected during "
                          "this assessment run.", STYLES["muted"])]
    rows: list[tuple[str, str]] = []
    for key, value in evidence.items():
        if key in _SKIP_KEYS:
            continue
        label = key.replace("_", " ").capitalize()
        if isinstance(value, dict) and "uri" in value:
            rows.append((label, f"artefact {value.get('artefact_type') or ''} "
                                f"— {value['uri']}".strip()))
        else:
            rows.append((label, str(value)))
    if not rows:
        return [Paragraph("No evidence documents were produced for this section.",
                          STYLES["muted"])]
    return [kv_table(rows)]
def _measured(rows: list[tuple[str, str]], caption: str) -> list[Any]:
    """Render a measured block, or say plainly that nothing was measured."""
    if not rows:
        return [Paragraph("No measurements were recorded for this section.",
                          STYLES["muted"])]
    return [Paragraph(caption, STYLES["h2"]), kv_table(rows)]


__all__ = ["_SKIP_KEYS", "_document", "_measured"]
