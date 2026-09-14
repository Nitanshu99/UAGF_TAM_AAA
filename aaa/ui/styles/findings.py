"""Finding-row display component."""
from __future__ import annotations

import html
from typing import Any

import streamlit as st

#: Finding materiality → the pill tone that names its severity.
_MATERIALITY_TONE: dict[str, str] = {
    "material": "is-bad",
    "possibly_material": "is-warn",
    "observation": "is-info",
}

#: Materiality → the words a reader sees. "possibly_material" is not English.
_MATERIALITY_LABEL: dict[str, str] = {
    "material": "Material",
    "possibly_material": "Possibly material",
    "observation": "Observation",
}


def finding_row(finding: dict[str, Any], index: int = 0) -> None:
    """Render a single finding with a materiality-coloured edge and chip.

    :param finding: Finding dict with ``finding_id`` / ``description`` /
        ``materiality`` / ``eu_ai_act_articles``.
    :param index: Position in the list, used to stagger the entry animation.
    """
    materiality = str(finding.get("materiality", "observation"))
    cls = materiality if materiality in _MATERIALITY_TONE else "observation"
    tone = _MATERIALITY_TONE.get(materiality, "is-info")
    label = _MATERIALITY_LABEL.get(materiality, materiality.replace("_", " "))
    fid = html.escape(str(finding.get("finding_id", "")))
    desc = html.escape(str(finding.get("description", "")))
    arts = ", ".join(html.escape(str(a)) for a in finding.get("eu_ai_act_articles", []))
    st.markdown(
        f'<div class="aaa-finding {cls}" style="--i:{index}">'
        f'<span class="fid">{fid}</span> '
        f'<span class="aaa-pill {tone}">{html.escape(label)}</span>'
        f'<div class="body">{desc}</div>'
        f'<div class="refs">{arts}</div>'
        "</div>",
        unsafe_allow_html=True,
    )
