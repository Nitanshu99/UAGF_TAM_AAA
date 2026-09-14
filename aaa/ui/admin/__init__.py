"""The auditor-facing console.

Everything the pipeline produces that is addressed to *us* rather than to the
customer: the HITL review packet and the command that closes it, the T17/T18
artefacts, the run-integrity record, the evidence status of each independent
analysis, and the AuditState itself.

It is one click from the customer's dashboard and nowhere else, so no part of
the customer's reading order has to make room for it.
"""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.platform.state.run_integrity import build_run_integrity
from aaa.ui.admin.artefacts import render_artefact_downloads
from aaa.ui.admin.header import render_admin_header
from aaa.ui.admin.hitl import render_hitl_panel
from aaa.ui.admin.run import render_run_record
from aaa.ui.wizard.step4.dossier import render_dossier
from aaa.ui.wizard.step4.evidence import render_evidence_status
from aaa.ui.wizard.step4.findings import render_findings
from aaa.ui.wizard.step4.integrity import render_integrity_banner
from aaa.ui.wizard.step4.matrix import render_matrix


def render_admin() -> None:
    """Render the admin console for the run held in session state."""
    final: dict | None = st.session_state.get("audit_result")
    eid: str = st.session_state.get("engagement_id", "—")
    render_admin_header(eid, final)
    if final is None:
        st.info("No completed run in this session. Finish an audit to inspect it here.")
        return
    store: EvidenceStore = st.session_state.get(
        "audit_store", st.session_state.get("aaa_evidence_store"))
    integrity = render_integrity_banner(final) or build_run_integrity(final)

    review, artefacts, detail = st.tabs(
        ["Review & sign-off", "Artefacts", "Findings & evidence"])
    with review:
        render_hitl_panel(eid, final)
        render_run_record(final, integrity)
    with artefacts:
        render_artefact_downloads(eid, final, store, integrity)
    with detail:
        render_matrix(final)
        render_findings(final)
        render_evidence_status(final)
        render_dossier(final)


__all__ = ["render_admin"]
