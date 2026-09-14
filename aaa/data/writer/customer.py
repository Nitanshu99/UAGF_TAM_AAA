"""Persist customer-facing deliverables under ``data/customer/<company>/``."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aaa.data.paths import customer_dir
from aaa.data.writer.atomic import _write, normalized_company_name
from aaa.data.writer.client_brief import _write_client_brief
from aaa.data.writer.deliverables import write_deliverables
from aaa.data.writer.integrity_stamp import stamp_integrity

logger = logging.getLogger(__name__)




def save_customer_artefacts(engagement_id: str, final_state: dict[str, Any],
                            store: Any) -> Path | None:
    """Persist ``<id>_audit_state.json`` / ``_T17.json`` / ``_T18.json``.

    The company folder is derived from the provider name in the client
    submission; T17/T18 payloads are resolved from the evidence *store* via
    the phase-artefact URIs.  Best-effort: a failure here is logged and must
    never break a completed run.

    :param engagement_id: Engagement identifier.
    :param final_state: Final ``AuditState``.
    :param store: Evidence store for URI resolution.
    :returns: The company directory, or ``None`` if nothing could be written.
    """
    try:
        stage_a = (final_state.get("client_submission") or {}).get("stage_a") or {}
        cdir = customer_dir(normalized_company_name(stage_a.get("provider_name")))
        stamp_integrity(final_state, engagement_id, store)
        _write(cdir / f"{engagement_id}_audit_state.json", final_state)

        artefacts = final_state.get("phase_artefacts") or {}
        deliverables = write_deliverables(cdir, engagement_id, artefacts,
                                          final_state, store)
        _write_client_brief(cdir, engagement_id, artefacts, store)

        if deliverables.get("T18") is not None:
            from aaa.tools.report_render.pdf.builder import build_pdf
            pdf = build_pdf(deliverables["T18"], deliverables.get("T17"),
                            final_state, store)
            (cdir / f"{engagement_id}_audit_report.pdf").write_bytes(pdf)

        # Last, so the archive captures the folder exactly as delivered.
        from aaa.data.writer.archive import archive_run
        archive_run(cdir, engagement_id, final_state)

        logger.info("Saved customer artefacts: %s → %s", engagement_id, cdir)
        return cdir
    except Exception as exc:  # noqa: BLE001 - never break a completed run
        logger.warning("Customer export failed for %s: %s", engagement_id, exc)
        return None
