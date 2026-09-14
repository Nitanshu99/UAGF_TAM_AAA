"""Wizard step 2 — Quick Questions the agent cannot answer from documents."""
from __future__ import annotations

import streamlit as st

from aaa.ui.styles import section_title
from aaa.ui.wizard.step2.form import QUESTION_COUNT, render_questions


def render_step_2() -> None:
    """Render the eight-question form and store the answers on submit."""
    # M25 was "8 Quick Questions" over seven questions numbered 1,2,3,5,6,7,8.
    # Adding 4a reintroduced the same mismatch, so the count is no longer
    # written by hand — `QUESTION_COUNT` is asserted against what step 2 renders.
    section_title("A few things only you can tell us",
                  f"{QUESTION_COUNT} questions our agents cannot answer from "
                  "documents — they are about how your system is used, not how "
                  "it is built. Two minutes.")
    with st.form("step2_questions"):
        answers = render_questions()
        st.divider()
        col_back, col_fwd, _ = st.columns([1, 1.6, 2])
        with col_back:
            back = st.form_submit_button("←  Back", use_container_width=True)
        with col_fwd:
            proceed = st.form_submit_button("Continue  →", type="primary",
                                            use_container_width=True)

    if back:
        st.session_state["step"] = 1
        st.rerun()
    if proceed:
        st.session_state["questionnaire_answers"] = answers
        st.session_state["step3_initialized"] = False
        st.session_state["step"] = 3
        st.rerun()
