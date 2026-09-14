"""Stage B data-dictionary inputs (target / label / sensitive / actionable features).

When a CSV dataset has been uploaded, its header row (captured in
``s3_dataset_columns``) drives column select-boxes; otherwise free-text
inputs are shown.

Fix F7 adds the two counterfactual-constraint fields. Without them DiCE infers
which features a subject could plausibly change from their *names*, which is how
a counterfactual explanation ends up advising a rejected applicant to be younger.
The S6 sheet asks that the two sets not conflict; nothing enforced that, so the
overlap is checked here — at the only point where the person who knows the
answer is present.
"""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.step3.fairness_precheck import _actionability_inputs, _fairness_precheck
from aaa.ui.wizard.step3.ranking_columns import render_ranking_columns


def render_data_dictionary() -> None:
    """Render the data-dictionary inputs, column-aware when headers are known."""
    st.markdown("#### Data dictionary (recommended)")
    st.caption(
        "Declare your dataset's semantics so the auditor need not infer them — "
        "this avoids assumption findings and drives the Art. 10 / Art. 15 fairness analysis."
    )
    columns = st.session_state.get("s3_dataset_columns") or []
    if columns:
        st.selectbox("Target column", options=["", *columns], key="s3_b_dd_target_sel",
                     help="Name of the column the model predicts — from your uploaded dataset.")
        st.multiselect("Sensitive feature columns", options=columns, key="s3_b_dd_sensitive_ms",
                       help="Protected attributes for non-discrimination testing, "
                            "e.g. age, sex, nationality. A continuous attribute is "
                            "binned into bands before any fairness metric sees it.")
    else:
        st.text_input("Target column", key="s3_b_dd_target",
                      help="Name of the column the model predicts, e.g. 'credit_risk'.")
        st.text_input("Sensitive feature columns (comma-separated)", key="s3_b_dd_sensitive",
                      help="Protected attributes for non-discrimination testing, "
                           "e.g. 'age, personal_status, foreign_worker'.")
    st.text_input("Favourable / positive label", key="s3_b_dd_positive",
                  help="The positive outcome value used for fairness analysis, e.g. '1'.")
    render_ranking_columns(columns)
    if columns:
        _fairness_precheck(list(st.session_state.get("s3_b_dd_sensitive_ms") or []))
        _actionability_inputs(columns)
