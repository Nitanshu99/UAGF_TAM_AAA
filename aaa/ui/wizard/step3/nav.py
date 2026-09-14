"""Navigation and run-gate controls for wizard step 3."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.collect import collect_stage_a, collect_stage_b
from aaa.ui.wizard.step3.blockers import _blockers


def render_navigation(score, gate) -> None:
    """Render back / run buttons and the 0.80 completeness gate.

    The run button is deliberately never disabled. A disabled primary button is
    the form anti-pattern the guidance names outright: it tells a customer they
    may not proceed without telling them why, and it makes the page scold
    someone who has only just arrived and has not filled anything in yet.
    Instead the click always does something — it either starts the audit or
    lists exactly what is in the way — and the reasons appear only once the
    customer has actually tried.

    :param score: Live completeness score (may be ``None``).
    :param gate: Scope-gate result with ``halt_engagement``.
    """
    st.divider()
    col_back, col_fwd, _ = st.columns([1, 1.8, 2])
    with col_back:
        if st.button("←  Back", use_container_width=True):
            st.session_state["step"] = 2
            st.rerun()
    with col_fwd:
        reasons = _blockers(score, gate)
        if st.button("Confirm & run my audit  →", type="primary",
                     use_container_width=True):
            if not reasons:
                st.session_state["step4_stage_a"] = collect_stage_a()
                st.session_state["step4_stage_b"] = collect_stage_b()
                st.session_state["step"] = 4
                st.rerun()
            st.session_state["s3_run_attempted"] = True
    if reasons and st.session_state.get("s3_run_attempted"):
        st.warning("**Not quite ready to run:**\n\n"
                   + "\n".join(f"- {reason}" for reason in reasons))
