"""Cached JSON loaders and upload/session-state helpers for the wizard."""
from __future__ import annotations

import json
from typing import Any

import streamlit as st

from aaa.platform.evidence import EvidenceStore
from aaa.ui.wizard.constants import FIXTURE_DIR, TEMPLATES_DIR


@st.cache_data(show_spinner=False)
def load_schema(name: str) -> dict:
    """Load a JSON template schema from ``templates/``.

    :param name: Schema filename, e.g. ``"T01a_stage_a_triage.json"``.
    :returns: Parsed schema dictionary.
    """
    return json.loads((TEMPLATES_DIR / name).read_text())


@st.cache_data(show_spinner=False)
def load_fixture(name: str) -> dict:
    """Load a bundled demo fixture, returning ``{}`` when absent.

    :param name: Fixture filename, e.g. ``"stage_c.json"``.
    :returns: Parsed fixture dictionary or an empty dict.
    """
    path = FIXTURE_DIR / name
    return json.loads(path.read_text()) if path.exists() else {}


def store_uploaded_file(
    store: EvidenceStore, engagement_id: str, role: str, uploaded: Any,
) -> str | None:
    """Persist a Streamlit upload into the EvidenceStore.

    :param store: Target evidence store.
    :param engagement_id: Engagement the file belongs to.
    :param role: Artefact role key, e.g. ``"model_metadata_uri"``.
    :param uploaded: Streamlit ``UploadedFile`` (``None`` is a no-op).
    :returns: The stored artefact URI, or ``None`` when nothing was uploaded.
    """
    if uploaded is None:
        return None
    return store.store_file(
        engagement_id=engagement_id,
        phase="customer_uploads",
        artefact_type=role,
        filename=uploaded.name,
        content_type=getattr(uploaded, "type", None) or "application/octet-stream",
        data=uploaded.getvalue(),
        agent_name="streamlit",
    )


def init_key(key: str, default: Any) -> None:
    """Set a session-state key only on first call — never overwrite an edit.

    :param key: Session-state key.
    :param default: Initial value used when the key is unset.
    """
    if key not in st.session_state:
        st.session_state[key] = default
