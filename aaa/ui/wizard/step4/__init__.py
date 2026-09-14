"""Wizard step 4 — run the audit, then show the customer their dashboard.

Reading order is the customer's, not the pipeline's: the conclusion first, the
numbers behind it, then the documents they came for, then the detail. Nothing
on this page names an artefact, a phase, or a template id; everything that does
is one click away in the admin console.
"""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.platform.state.run_integrity import build_run_integrity
from aaa.ui.wizard.step4.articles import render_articles
from aaa.ui.wizard.step4.deliverables import render_deliverables
from aaa.ui.wizard.step4.kpis import render_kpis
from aaa.ui.wizard.step4.nextsteps import render_next_steps
from aaa.ui.wizard.step4.run import execute_pipeline
from aaa.ui.wizard.step4.status import render_opinion, render_status
from aaa.ui.wizard.step4.topbar import render_topbar
from aaa.ui.wizard.step4.verdict import render_verdict


def render_step_4() -> None:
    """Render the results dashboard (runs the pipeline on first arrival)."""
    store: EvidenceStore = st.session_state["aaa_evidence_store"]
    eid: str = st.session_state["engagement_id"]
    if "audit_result" not in st.session_state and not execute_pipeline(eid, store):
        return

    final: dict = st.session_state["audit_result"]
    store = st.session_state.get("audit_store", store)
    integrity = final.get("run_integrity") or build_run_integrity(final)

    render_topbar(eid)
    render_verdict(eid, final)
    st.write("")
    render_kpis(final)
    degraded = render_status(final, integrity)
    render_deliverables(eid, final, store, degraded)
    render_opinion(final)
    render_articles(final)
    render_next_steps(final)
    _restart()


def _restart() -> None:
    """Offer a clean slate, without making it look like the primary action."""
    st.markdown('<hr>', unsafe_allow_html=True)
    if st.button("Start another audit"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
