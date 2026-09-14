"""The wizard's progress rail.

An ordered list, because that is what it is: five named steps in sequence with
one of them current. The rail's filled portion is a plain element whose width
is a percentage, so the fill animates on every rerun without any script.
"""
from __future__ import annotations

import html

import streamlit as st


def _node(index: int, label: str, step: int) -> str:
    """Render one step node in its done / current / todo state."""
    state = "done" if index < step else "current" if index == step else "todo"
    mark = "✓" if state == "done" else str(index + 1)
    current = ' aria-current="step"' if state == "current" else ""
    return (f'<li class="aaa-step-node" data-state="{state}"{current}>'
            f'<span class="aaa-step-dot" aria-hidden="true">{mark}</span>'
            f'<span class="aaa-step-label">{html.escape(label)}</span></li>')


def render_stepper(step: int, labels: list[str]) -> None:
    """Render the progress rail above the active wizard step.

    :param step: Zero-based index of the active step.
    :param labels: Step names, in order.
    """
    span = max(len(labels) - 1, 1)
    pct = 100.0 * min(max(step, 0), span) / span
    nodes = "".join(_node(i, label, step) for i, label in enumerate(labels))
    st.markdown(
        f'<nav aria-label="Audit progress"><ol class="aaa-stepper">'
        f'<span class="aaa-step-rail" aria-hidden="true">'
        f'<span class="aaa-step-rail-fill" style="inline-size:{pct:.0f}%"></span></span>'
        f"{nodes}</ol></nav>",
        unsafe_allow_html=True)
