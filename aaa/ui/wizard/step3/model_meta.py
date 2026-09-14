"""Stage B model-metadata inputs (S6 hand-off): task type, format, framework.

Select-boxes are pre-filled from the uploaded model filename
(:func:`aaa.tools.model_meta.infer_model_format`) and the Stage A declared
modality (:func:`aaa.tools.model_meta.suggest_task_type`); users can override.
"""
from __future__ import annotations

import streamlit as st

from aaa.platform.state.model_vocab import MODEL_FORMATS, MODEL_FRAMEWORKS, TASK_TYPES
from aaa.tools.model_meta import infer_model_format, suggest_task_type
from aaa.ui.wizard.step3.artifact_layout import _prefill, render_artifact_layout


def render_model_meta() -> None:
    """Render the task-type / model-format / framework select-boxes."""
    st.markdown("#### Model metadata (required for model evaluation)")
    st.caption("Tells the auditor how to load and evaluate the model artefact (Art. 15).")
    model_uri = (st.session_state.get("s3_b_uris") or {}).get("model_artifact_uri")
    fmt, framework = infer_model_format(model_uri)
    _prefill("s3_b_model_format", fmt)
    _prefill("s3_b_model_framework", framework)
    _prefill("s3_b_task_type",
             suggest_task_type(st.session_state.get("s3_a_declared_modality")))
    st.selectbox("Task type", options=("", *TASK_TYPES), key="s3_b_task_type",
                 help="What the model does. Required when a model artefact is uploaded.")
    st.selectbox("Model format", options=("", *MODEL_FORMATS), key="s3_b_model_format",
                 help="Serialisation format of the model artefact — pre-filled from the "
                      "uploaded filename. Required when a model artefact is uploaded.")
    st.selectbox("Model framework (optional)", options=("", *MODEL_FRAMEWORKS),
                 key="s3_b_model_framework",
                 help="Library required to run the model, e.g. sklearn. Pick the "
                      "wrapper or adapter variant when there is one — a Chronos "
                      "wrapper declared as bare sklearn loads as the wrong object.")
    render_artifact_layout()
