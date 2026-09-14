"""Stage B free-text documentation widgets for wizard step 3."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.progress import field_caption
from aaa.ui.wizard.step3.stage_b.metrics import render_metrics_field
from aaa.ui.wizard.step3.stage_b.spec import _TEXT_FIELDS


def render_descriptions(confidence: dict, sources: dict, missing: list) -> None:
    """Render the Annex IV free-text fields.

    :param confidence: Extraction confidence per field.
    :param sources: Extraction source document per field.
    :param missing: Fields the extraction could not find.
    """
    for field, (label, help_text, placeholder, height) in _TEXT_FIELDS.items():
        key = f"s3_b_{field}"
        if height is None:
            st.text_input(label, key=key, help=help_text, placeholder=placeholder)
        else:
            st.text_area(label, key=key, help=help_text, placeholder=placeholder, height=height)
        field_caption(field, confidence, sources, missing)


def render_metrics_and_standards(confidence: dict, sources: dict, missing: list) -> None:
    """Render metrics JSON, change log, and standards inputs."""
    render_metrics_field(confidence, sources, missing)

    st.text_area(
        "Significant changes log (one change per line)", key="s3_b_lifecycle_change_log_raw",
        help="Annex IV §6 — Significant changes since initial deployment, one per line. "
             "E.g. 'v1.1 — Retrained on 2024 data to reduce demographic bias'.",
        placeholder="v1.1 — Retrained on 2024 data\nv1.2 — Threshold adjusted for fairness", height=70)

    st.text_input(
        "Harmonised standards applied (comma-separated)", key="s3_b_harmonised_standards_raw",
        help="Annex IV §7 — ISO, IEC, or EU harmonised standards. "
             "E.g. 'ISO/IEC 42001:2023, ISO/IEC 23894:2023'.",
        placeholder="ISO/IEC 42001:2023, ISO/IEC 23894:2023")
    field_caption("harmonised_standards", confidence, sources, missing)

    st.text_input(
        "Other standards applied (comma-separated)", key="s3_b_other_standards_raw",
        help="Annex IV §7 — Other technical or sector-specific standards applied.",
        placeholder="e.g. EBA/GL/2020/06, ISO 31000:2018")

    st.text_input(
        "Tool inventory (comma-separated)", key="s3_b_tool_inventory_raw",
        help="Agentic only — Names of tools/functions the system may call, e.g. "
             "'web_search, code_executor, send_email'. Used to flag unauthorised "
             "tool calls during the trajectory audit.",
        placeholder="web_search, code_executor, send_email")
    field_caption("tool_inventory", confidence, sources, missing)
