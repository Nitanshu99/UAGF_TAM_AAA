"""Stage A boolean flags for wizard step 3.

The CGSA assessment reference used to be a text input here. It asked the
customer to quote an identifier S4 mints and never shows them; it is now
looked up from the provider and system names they have already given
(:func:`aaa.tools.cgsa_pull.resolve_assessment_id`).
"""
from __future__ import annotations

import streamlit as st


def render_flags() -> None:
    """Render the GDPR / GPAI / third-party declaration checkboxes."""
    st.checkbox(
        "System processes personal data (GDPR overlap)", key="s3_a_gdpr_overlap",
        help="Does the system use or produce data that identifies individuals? "
             "Triggers GDPR Art. 35 / DPIA review.")
    st.checkbox(
        "System processes special-category data", key="s3_a_special_category_data",
        help="Health records, biometrics, political/religious beliefs, racial/ethnic origin — "
             "see GDPR Art. 9 and EU AI Act Art. 10 §5.")
    st.checkbox(
        "This is a General-Purpose AI (GPAI) model", key="s3_a_gpai_general_purpose",
        help="A foundation model or LLM designed to handle many different tasks (Arts. 51–55 EU AI Act).")
    st.checkbox(
        "Elect voluntary third-party conformity assessment", key="s3_a_provider_elects_third_party",
        help="Art. 43 §1(b) — Choose to have a notified body independently verify compliance "
             "even if not legally required.")
