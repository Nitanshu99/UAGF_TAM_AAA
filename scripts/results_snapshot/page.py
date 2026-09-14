"""The Streamlit page the snapshot renders: the customer dashboard over a saved AuditState.

Run by :mod:`scripts.results_snapshot` with ``AAA_SNAPSHOT_STATE`` pointing at an
``*_audit_state.json``. It renders exactly what wizard step 4 renders, from the
state the run wrote, so an API-driven run gets the same results page a wizard run
shows — without re-running anything.
"""
from __future__ import annotations

import json
import os
import pathlib

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui import styles
from aaa.ui.wizard.step4 import render_step_4


def main() -> None:
    """Load the saved state into the session and render the dashboard."""
    st.set_page_config(page_title="EU AI Act Conformity Audit", page_icon="✓", layout="wide")
    styles.inject_theme()
    if "audit_result" not in st.session_state:
        final = json.loads(pathlib.Path(os.environ["AAA_SNAPSHOT_STATE"]).read_text("utf-8"))
        st.session_state["audit_result"] = final
        st.session_state["engagement_id"] = final.get("engagement_id") or "engagement"
        st.session_state["aaa_evidence_store"] = EvidenceStore()
    render_step_4()


main()
