"""Pipeline execution for wizard step 4 (run once, cache the final state)."""
from __future__ import annotations

import asyncio
import logging

import streamlit as st

from aaa.agents.intake_validator import IntakeValidatorError
from aaa.platform.evidence import EvidenceStore
from aaa.ui.wizard.loaders import load_fixture
from aaa.ui.wizard.pipeline import run_pipeline
from aaa.ui.wizard.step4.persist import _intake_failed, _persist
from aaa.ui.wizard.step4.running import render_running

logger = logging.getLogger(__name__)


def execute_pipeline(eid: str, store: EvidenceStore) -> bool:
    """Run the audit once and cache the result; returns False on gate failure.

    :param eid: Engagement identifier.
    :type eid: str
    :param store: Evidence store for the engagement.
    :type store: EvidenceStore
    :returns: ``True`` when a final state was produced and cached.
    :rtype: bool
    """
    stage_a: dict = st.session_state["step4_stage_a"]
    stage_b: dict = st.session_state["step4_stage_b"]
    stage_c: dict | None = load_fixture("stage_c.json") or None
    # Into a placeholder, not straight onto the page: the dashboard renders in
    # the same script pass that ran the pipeline, so a bare `st.markdown` here
    # leaves "We are auditing Mariposa." sitting above the finished results
    # until the next rerun — which for a customer reads as an audit that never
    # stopped running.
    waiting = st.empty()
    with waiting.container():
        render_running(str(stage_a.get("system_name") or ""))
    with st.spinner("Working through your dossier…"):
        try:
            final = asyncio.run(run_pipeline(eid, stage_a, stage_b, stage_c, store))
        except IntakeValidatorError as exc:
            waiting.empty()
            _intake_failed(exc)
            return False
    waiting.empty()
    _persist(eid, final, store)
    st.session_state["audit_result"] = final
    st.session_state["audit_store"] = store
    return True
