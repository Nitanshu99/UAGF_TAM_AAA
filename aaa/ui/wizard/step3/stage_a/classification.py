"""Stage A classification widgets: modality, risk tier, Annex III, context."""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.constants import ANNEX_III_LABELS
from aaa.ui.wizard.progress import field_caption

#: What an undeclared select shows instead of preselecting an option.
PLACEHOLDER = "Choose one"


def _ensure_valid(key: str, options: list[str]) -> None:
    """Clear a select key whose value is not one of its options.

    It used to reset to ``options[0]``, which turned an extraction the schema
    rejects into a declaration of ``tabular`` or ``high`` the provider never made
    (T-20260914-021). Cleared, the select shows :data:`PLACEHOLDER` and the run
    stays blocked until the provider chooses.
    """
    if st.session_state.get(key) not in options:
        st.session_state[key] = None


def render_classification(schema_props: dict, confidence: dict, sources: dict, missing: list) -> None:
    """Render modality / risk-tier / Annex III / deployment-context widgets.

    :param schema_props: ``properties`` of the T01a schema (enum sources).
    :param confidence: Extraction confidence per field.
    :param sources: Extraction source document per field.
    :param missing: Fields the extraction could not find.
    """
    modality_opts = schema_props.get("declared_modality", {}).get(
        "enum", ["tabular", "cv", "nlp", "time_series", "llm", "agentic", "gpai"])
    _ensure_valid("s3_a_declared_modality", modality_opts)
    st.selectbox(
        "AI modality", options=modality_opts, key="s3_a_declared_modality",
        index=None, placeholder=PLACEHOLDER,
        help="Primary technical type of this AI system. tabular = structured data / classical ML, "
             "cv = computer vision, nlp = text/language processing, time_series = forecasting, "
             "llm = large language model, agentic = autonomous agent system, "
             "gpai = general-purpose foundation model.")
    field_caption("declared_modality", confidence, sources, missing)

    tier_opts = schema_props.get("declared_risk_tier", {}).get("enum", ["high", "limited", "minimal", "gpai"])
    _ensure_valid("s3_a_declared_risk_tier", tier_opts)
    st.selectbox(
        "Self-assessed risk tier", options=tier_opts, key="s3_a_declared_risk_tier",
        index=None, placeholder=PLACEHOLDER,
        help="Art. 6 — Your own assessment of the risk tier. high = Annex III use case "
             "(most obligations), limited = transparency obligations only (Art. 50), "
             "minimal = no specific EU AI Act obligations, gpai = general-purpose AI model (Arts. 51–55).")
    field_caption("declared_risk_tier", confidence, sources, missing)

    st.multiselect(
        "Annex III high-risk categories", options=list(ANNEX_III_LABELS.values()),
        key="_s3_annex_iii_labels",
        help="Art. 6 §2 — Select every Annex III category that applies to your system. At least one "
             "selection triggers high-risk obligations unless Art. 6 §3 derogation applies.")
    keys, vals = list(ANNEX_III_LABELS.keys()), list(ANNEX_III_LABELS.values())
    st.session_state["s3_a_declared_annex_iii_sections"] = [
        keys[vals.index(lbl)] for lbl in (st.session_state.get("_s3_annex_iii_labels") or [])]

    deployment_opts = ["b2b", "b2c", "public_sector", "internal"]
    _ensure_valid("s3_a_deployment_context", deployment_opts)
    st.selectbox(
        "Deployment context", options=deployment_opts, key="s3_a_deployment_context",
        index=None, placeholder=PLACEHOLDER,
        help="Who uses this system directly? b2b = sold to/used by other businesses, "
             "b2c = used directly by consumers, public_sector = government or public authority, "
             "internal = used only within your own organisation.")
