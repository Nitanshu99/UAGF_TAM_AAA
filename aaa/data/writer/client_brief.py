"""Writing the Agent 14 client brief into the customer folder, as Markdown and as PDF."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _write_client_brief(cdir: Path, engagement_id: str,
                        artefacts: dict[str, Any], store: Any) -> None:
    """Write the plain-language brief as ``<id>_client_report.md``.

    This is the only deliverable in the folder the customer can read without an
    auditor beside them, so its absence is logged rather than passed over: a
    silent skip here looks identical to a run that was never asked for one.
    """
    from aaa.agents.tier2.client_brief import TEMPLATE_ID
    ref = artefacts.get(TEMPLATE_ID)
    uri = ref.get("uri") if isinstance(ref, dict) else None
    payload = store.get_artefact(uri) if uri else None
    body = (payload or {}).get("body") if isinstance(payload, dict) else None
    if not body:
        logger.warning("Customer export: %s has no client brief; the folder holds "
                       "only the formal report.", engagement_id)
        return
    (cdir / f"{engagement_id}_client_report.md").write_text(body, encoding="utf-8")
    # The customer folder is what gets sent on; the brief is the file in it a
    # non-specialist actually reads, so it ships as a PDF too rather than as
    # Markdown only. A render failure costs the PDF, never the Markdown.
    try:
        from aaa.tools.report_render.pdf.brief import build_brief_pdf
        (cdir / f"{engagement_id}_client_brief.pdf").write_bytes(
            build_brief_pdf(body, engagement_id))
    except Exception as exc:  # noqa: BLE001 - the Markdown deliverable stands
        logger.warning("Client brief PDF render failed for %s: %s", engagement_id, exc)


__all__ = ["_write_client_brief"]
