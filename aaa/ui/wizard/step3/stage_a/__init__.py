"""Stage A core widgets for wizard step 3 (identity and purpose)."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.progress import field_caption


def render_identity(confidence: dict, sources: dict, missing: list) -> None:
    """Render provider / system / version / purpose inputs.

    :param confidence: Extraction confidence per field.
    :param sources: Extraction source document per field.
    :param missing: Fields the extraction could not find.
    """
    st.text_input(
        "Legal provider name", key="s3_a_provider_name",
        help="Art. 11 — Full legal name of the organisation that developed or places "
             "this AI system on the market. E.g. 'Acme Analytics GmbH'",
        placeholder="e.g. Acme Analytics GmbH")
    field_caption("provider_name", confidence, sources, missing)

    st.text_input(
        "System name", key="s3_a_system_name",
        help="Commercial or internal name used to identify this AI system. E.g. 'CreditScoreRef v2'",
        placeholder="e.g. CreditScoreRef v2")
    field_caption("system_name", confidence, sources, missing)

    st.text_input(
        "Version", key="s3_a_version",
        help="Semantic version number (major.minor or major.minor.patch). "
             "Acceptable: 2.1, 2.1.0, v2.1, V2.1.0 (leading 'v'/'V' is automatically removed).",
        placeholder="e.g. 2.1.0 or v2.1.0")
    field_caption("version", confidence, sources, missing)

    st.text_area(
        "Intended purpose", key="s3_a_intended_purpose",
        help="Art. 13 — Describe what this system is designed to do, who uses it, "
             "and in what context. Minimum 20 characters.",
        placeholder="e.g. Automated credit-scoring for retail banking customers in the EU "
                    "to support loan eligibility decisions.",
        height=90)
    field_caption("intended_purpose", confidence, sources, missing)
