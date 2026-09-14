"""Wizard step 1 — Upload Documents and run document intelligence."""
from __future__ import annotations

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.styles import note, section_title
from aaa.ui.wizard.step1.actions import persist_and_extract
from aaa.ui.wizard.step1.widgets import render_uploaders


def render_step_1() -> None:
    """Render the document-upload step."""
    section_title("What have you got?",
                  "Anything that describes your AI system. These are the "
                  "documents our auditors read and quote as evidence, so the "
                  "more you give us, the more of the audit is measured rather "
                  "than taken on trust.")
    store: EvidenceStore = st.session_state["aaa_evidence_store"]
    eid: str = st.session_state["engagement_id"]
    doc_files, model_file, dataset_files = render_uploaders()
    can_proceed = bool(doc_files or model_file or dataset_files)
    if not can_proceed:
        note("info", "↑", "Nothing uploaded yet",
             "You can carry on without uploading anything. A thin dossier is "
             "itself something the audit reports on — several articles come "
             "back as “could not be checked” rather than as a pass.")
    st.write("")
    col_back, col_fwd, _ = st.columns([1, 1.6, 2])
    with col_back:
        if st.button("←  Back", use_container_width=True):
            st.session_state["step"] = 0
            st.rerun()
    with col_fwd:
        label = "File my documents  →" if can_proceed else "Continue without them  →"
        if st.button(label, type="primary" if can_proceed else "secondary",
                     use_container_width=True):
            persist_and_extract(store, eid, doc_files, model_file, dataset_files)
