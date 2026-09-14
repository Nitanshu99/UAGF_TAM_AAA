"""Headings and the running total for the upload bands."""
from __future__ import annotations

import html

import streamlit as st


def band_heading(title: str, blurb: str) -> None:
    """Head one group of uploaders with what it is for.

    :param title: The group name.
    :param blurb: One sentence on why the group matters.
    """
    st.markdown(
        f'<div style="margin-block:1.5rem .6rem">'
        f'<div style="font-weight:620;font-size:1.02rem">{html.escape(title)}</div>'
        f'<p class="aaa-section-sub" style="font-size:.9rem;margin:.15rem 0 0">'
        f"{html.escape(blurb)}</p></div>", unsafe_allow_html=True)


def uploads_footer(supplied: int, total: int) -> None:
    """Show how many artefact slots hold a file.

    :param supplied: Slots with a stored URI.
    :param total: Slots offered.
    """
    st.markdown(
        f'<p class="aaa-muted" style="margin-block-start:1rem">'
        f"{supplied} of {total} document slots filled.</p>", unsafe_allow_html=True)
