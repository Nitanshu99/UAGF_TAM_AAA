"""Stage A advanced compliance fields (FLI EU AI Act Compliance Checker)."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.step3.stage_a.fli.spec import _EXCLUSION_OPTIONS, _MULTISELECTS


def render_fli_fields() -> None:
    """Render the optional FLI compliance-checker fields in an expander."""
    with st.expander("Advanced compliance fields (FLI EU AI Act Compliance Checker)", expanded=False):
        st.caption(
            "These fields are derived from the Future of Life Institute EU AI Act Compliance "
            "Checker. All are optional — populate them for a more precise scope gate."
        )
        for label in ("FLI-E2 · Art. 25 modifications (triggers Provider status)",
                      "FLI-HR1 · Annex I Section B sectoral categories",
                      "FLI-HR2 · Annex I Section A product categories"):
            key, options = _MULTISELECTS[label]
            st.multiselect(label, options=options, key=key)
        st.checkbox("FLI-HR3 · Third-party conformity assessment legally required",
                    key="s3_a_third_party_ca_legally_required")
        st.checkbox("FLI-HR5 · Art. 6 §3 derogation claimed (no significant risk of harm)",
                    key="s3_a_art6_derogation_claimed")
        if st.session_state.get("s3_a_art6_derogation_claimed"):
            st.text_area("Art. 6 §3 derogation rationale", key="s3_a_art6_derogation_rationale", height=70)
        st.checkbox("FLI-R1 · GPAI meets Art. 51 §2 systemic-risk threshold (>10^25 FLOPs)",
                    key="s3_a_gpai_systemic_risk")
        st.selectbox("FLI-R2 · Art. 2 exclusion category (if any)",
                     options=_EXCLUSION_OPTIONS, key="s3_a_art2_exclusion")
        for label in ("FLI-R3 · Art. 5 prohibited practices (any selection halts engagement)",
                      "FLI-R4 · Art. 50 transparency triggers"):
            key, options = _MULTISELECTS[label]
            st.multiselect(label, options=options, key=key)
        st.checkbox(
            "FLI-R5 · Public-law body or private entity providing public services",
            key="s3_a_is_public_body_or_public_service",
            help="Triggers Art. 27 Fundamental Rights Impact Assessment when combined with high risk.")
