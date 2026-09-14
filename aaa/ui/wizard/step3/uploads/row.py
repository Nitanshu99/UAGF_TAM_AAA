"""One Stage B file-uploader row and the side effects an upload triggers."""
from __future__ import annotations

from typing import Any

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.tools.model_meta import archive_members
from aaa.ui.wizard.loaders import store_uploaded_file
from aaa.ui.wizard.step3.csv_columns import csv_column_values, csv_header_columns

#: Upload keys whose CSV header feeds the data-dictionary column suggestions.
_DATASET_KEYS = ("training_dataset_uri", "evaluation_dataset_uri")

#: Upload key whose archive listing feeds the model-entrypoint select (F6).
_MODEL_KEY = "model_artifact_uri"


def capture_bundle_listing(uploaded: Any) -> None:
    """Record an uploaded model archive's members for the entrypoint control.

    Read here rather than at render time because the Streamlit upload is a
    stream: by the time the model-metadata section renders, this is the only
    place that still holds the bytes.

    :param uploaded: Streamlit ``UploadedFile`` for the model artefact.
    """
    st.session_state["s3_model_filename"] = uploaded.name
    st.session_state["s3_model_members"] = (
        archive_members(uploaded.getvalue())
        if uploaded.name.lower().endswith(".zip") else [])


def _remember_upload(key: str, uploaded: Any) -> None:
    """Capture what later sections need from *uploaded* while its bytes are here.

    :param key: Upload field key.
    :param uploaded: Streamlit ``UploadedFile``.
    """
    if key in _DATASET_KEYS and uploaded.name.lower().endswith(".csv"):
        st.session_state["s3_dataset_columns"] = csv_header_columns(uploaded)
        # F12: the values, not just the header — the fairness pre-check needs
        # to know whether a column is continuous and how small its cohorts
        # are, and this is the only point that still holds the bytes.
        st.session_state["s3_dataset_values"] = csv_column_values(uploaded)
    if key == _MODEL_KEY:
        capture_bundle_listing(uploaded)


def uploader_row(store: EvidenceStore, eid: str, key: str,
                 label: str, description: str, file_types: list[str], *, note_existing: bool) -> None:
    """Render one file-uploader row and persist its upload.

    :param store: Evidence store for persisted uploads.
    :param eid: Engagement identifier.
    :param key: Upload field key.
    :param label: Uploader label.
    :param description: Help text shown beside the uploader.
    :param file_types: Accepted file extensions.
    :param note_existing: Whether to mention an already-supplied upload.
    """
    uploaded = st.file_uploader(f"{label}", type=file_types, key=f"s3_upload_{key}", help=description)
    if uploaded:
        _remember_upload(key, uploaded)
        uri = store_uploaded_file(store, eid, key, uploaded)
        if uri:
            st.session_state.setdefault("s3_b_uris", {})[key] = uri
            st.caption(f"Uploaded: {uploaded.name}")
    elif note_existing and (st.session_state.get("s3_b_uris") or {}).get(key):
        st.caption("✓ Already supplied — upload again only to replace it.")


__all__ = ["capture_bundle_listing", "uploader_row"]
