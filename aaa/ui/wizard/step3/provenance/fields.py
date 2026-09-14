"""Widget rendering for one provenance question.

Questions are stored under ``s3_b_ref_<key>`` so the collector can assemble a
``model_reference`` without knowing which vendor branch produced it.
"""
from __future__ import annotations

import streamlit as st

#: Question keys rendered as a yes/no rather than free text.
_BOOLEAN_KEYS = frozenset({"gated"})
#: Question keys whose answers are structured enough to want more room.
_AREA_KEYS = frozenset({"decoding_params", "runtime_versions"})


def state_key(reference_key: str) -> str:
    """Return the session-state key holding *reference_key*'s answer.

    :param reference_key: A :class:`ModelReference` key.
    :type reference_key: str
    :returns: Namespaced widget key.
    :rtype: str
    """
    return f"s3_b_ref_{reference_key}"


def render_question(reference_key: str, label: str, help_text: str) -> None:
    """Render one vendor question as the widget its answer shape calls for.

    :param reference_key: The :class:`ModelReference` key it fills.
    :param label: Field label shown to the customer.
    :param help_text: Tooltip explaining what to supply and why.
    """
    key = state_key(reference_key)
    if reference_key in _BOOLEAN_KEYS:
        st.checkbox(label, key=key, help=help_text)
        return
    if reference_key in _AREA_KEYS:
        st.text_area(label, key=key, help=help_text, height=68)
        return
    st.text_input(label, key=key, help=help_text)
