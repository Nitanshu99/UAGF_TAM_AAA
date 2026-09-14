"""Raw artefact downloads: T17, T18, the rendered PDFs, the AuditState.

A degraded run keeps every one of these — a human diagnosing a failed pipeline
needs the files — but every filename gains a ``_DEGRADED`` marker so a file that
leaves this console carries the fact with it (F5, finding S3).
"""
from __future__ import annotations

import json

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.admin.client_documents import _client_documents
from aaa.ui.styles import note, section_title
from aaa.ui.wizard.step4.artefacts import template_json


def _json_button(label: str, payload: dict | list, filename: str) -> None:
    """Offer a JSON artefact for download."""
    st.download_button(label, data=json.dumps(payload, indent=2, default=str).encode(),
                       file_name=filename, mime="application/json")


def render_artefact_downloads(eid: str, final: dict, store: EvidenceStore,
                              integrity: dict) -> None:
    """Render every deliverable this run produced, unfiltered.

    :param eid: Engagement identifier.
    :param final: Final ``AuditState`` dictionary.
    :param store: Evidence store holding the rendered artefacts.
    :param integrity: The run's ``run_integrity`` block.
    """
    suffix = "" if integrity["suitable_for_handoff"] else "_DEGRADED"
    if suffix:
        note("warn", "⚠", "Degraded run — marked in every filename",
             "These files exist to diagnose the failure, not to be sent to a "
             "client. The client dashboard is already withholding them.")
    section_title("Client-facing documents",
                  "The same two PDFs the customer is offered on their dashboard.")
    left, right = st.columns(2, gap="medium")
    _client_documents(left, right, eid, final, store, suffix)
    section_title("Machine-readable artefacts",
                  "Template payloads and the full pipeline state.")
    a, b, c = st.columns(3, gap="medium")
    with a:
        _json_button("⬇ T17 compliance matrix",
                     template_json(final, store, "T17_compliance_matrix"),
                     f"{eid}{suffix}_T17.json")
    with b:
        _json_button("⬇ T18 audit report",
                     template_json(final, store, "T18_audit_report"),
                     f"{eid}{suffix}_T18.json")
    with c:
        _json_button("⬇ Full AuditState", final, f"{eid}{suffix}_audit_state.json")
