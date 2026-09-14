"""Upload widgets for wizard step 1.

The technical dossier gets the full width because it is the one upload that
changes the audit; the model and the datasets share the row below it, labelled
as what they buy rather than as what they are.
"""
from __future__ import annotations

import html

import streamlit as st


def _label(title: str, blurb: str, optional: bool = False) -> None:
    """Head one uploader with what it is for."""
    tag = ('<span class="aaa-pill is-none" style="margin-inline-start:.5rem">optional</span>'
           if optional else "")
    st.markdown(f'<div style="font-weight:620;margin-block:.2rem .15rem">'
                f"{html.escape(title)}{tag}</div>"
                f'<p class="aaa-section-sub" style="font-size:.88rem;margin-block-end:.5rem">'
                f"{html.escape(blurb)}</p>", unsafe_allow_html=True)


def render_uploaders() -> tuple[list, object, list]:
    """Render the three upload widgets and return their values."""
    _label("Technical documentation",
           "Model card, technical spec, data sheet, risk assessment, system "
           "description, performance metrics, policies — drop in everything "
           "you have.")
    doc_files = st.file_uploader(
        "Upload documents", accept_multiple_files=True,
        # `json` is accepted because `client_doc_ingest` already reads it
        # (`config._content_type`), and a real dossier carries JSON technical
        # documents — a metrics file, a model card, a retrieval manifest. Case 06
        # ships `performance_metrics.json` with measured latency and accuracy
        # figures that no other slot can take: the dataset uploaders would file
        # it as a dataset URI and overwrite one. Without this it was the one
        # client document the audit could not be given.
        type=["pdf", "docx", "doc", "txt", "md", "json"],
        key="step1_docs", label_visibility="collapsed")
    st.write("")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        _label("The model itself", "Lets us test accuracy, robustness and "
               "fairness rather than take your word for them.", optional=True)
        model_file = st.file_uploader(
            "Upload model", type=["pkl", "joblib", "onnx", "pt", "safetensors", "zip"],
            key="step1_model", label_visibility="collapsed")
    with col2:
        _label("Training or evaluation data", "Lets us check data governance and "
               "look for bias in what the model learned from.", optional=True)
        dataset_files = st.file_uploader(
            "Upload datasets", accept_multiple_files=True,
            type=["csv", "parquet", "json"],
            key="step1_datasets", label_visibility="collapsed")
    return doc_files, model_file, dataset_files
