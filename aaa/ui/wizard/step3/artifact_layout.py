"""The model-artefact layout controls: entrypoint, framework and how it is served."""
from __future__ import annotations

import streamlit as st

from aaa.platform.state.model_vocab import ARTIFACT_KINDS
from aaa.tools.model_meta import DIRECTORY, infer_artifact_kind, suggest_entrypoint


def _prefill(key: str, value: str | None) -> None:
    """Seed a widget default once, never overriding a user's edit.

    :param key: Session-state key of the widget.
    :type key: str
    :param value: Inferred default, ignored when falsy.
    :type value: str | None
    """
    if value and key not in st.session_state:
        st.session_state[key] = value
def render_artifact_layout() -> None:
    """Render the artefact-layout radio and, for a bundle, its entry point.

    A directory-shaped model (a Hugging Face snapshot, a Chronos wrapper)
    arrives as a ``.zip``; the members were read at upload time by
    :func:`aaa.ui.wizard.step3.uploads.row.capture_bundle_listing`, because the
    Streamlit upload is a stream that is gone by the time this renders.
    """
    filename = st.session_state.get("s3_model_filename")
    members: list[str] = st.session_state.get("s3_model_members") or []
    _prefill("s3_b_model_artifact_kind", infer_artifact_kind(filename))
    st.radio(
        "Model artefact layout", options=("", *ARTIFACT_KINDS),
        key="s3_b_model_artifact_kind", horizontal=True,
        format_func=lambda v: {"": "— not set —", "single_file": "One file",
                               "directory": "A directory (uploaded as .zip)"}[v],
        help="Whether the artefact is a single model file or a directory of files "
             "(weights plus config.json, an adapter, a wrapper). Pre-filled from "
             "the uploaded filename.")
    if st.session_state.get("s3_b_model_artifact_kind") != DIRECTORY:
        return
    _prefill("s3_b_model_entrypoint", suggest_entrypoint(members))
    entry_help = ("The file or sub-directory inside the bundle that is the model. "
                  "The auditor loads model_artifact_uri / model_entrypoint.")
    if members:
        options = ["", *members]
        current = st.session_state.get("s3_b_model_entrypoint")
        if current and current not in options:
            options.insert(1, current)
        st.selectbox("Model entry point", options=options,
                     key="s3_b_model_entrypoint", help=entry_help)
        st.caption(f"{len(members)} file(s) found in the uploaded archive.")
    else:
        st.text_input("Model entry point", key="s3_b_model_entrypoint",
                      placeholder="e.g. demandpulse_v3.0.joblib", help=entry_help)
    if not st.session_state.get("s3_b_model_entrypoint"):
        st.warning("A directory artefact needs an entry point — without it the "
                   "auditor cannot tell which file in the bundle is the model.")


__all__ = ["_prefill", "render_artifact_layout"]
