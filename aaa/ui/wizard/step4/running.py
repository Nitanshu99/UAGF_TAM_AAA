"""The screen the customer looks at while the audit actually runs.

This is the longest wait in the product — minutes — and it used to be a one-line
spinner reading "Running IntakeValidator → Orchestrator". Those are our class
names. What a person waiting needs is to know the wait is expected, that
something is happening, and roughly what.
"""
from __future__ import annotations

import html

import streamlit as st

_RUNNING_CSS = """
<style>
.aaa-run { display: grid; gap: .55rem; }
.aaa-run-step { display: grid; grid-template-columns: auto 1fr; gap: .7rem;
  align-items: center; color: var(--text-2); font-size: .93rem;
  animation: aaa-rise var(--dur-3) var(--ease) backwards;
  animation-delay: calc(var(--i) * 90ms);
  --anim-reduced: aaa-fade var(--dur-2) var(--ease) backwards; }
.aaa-run-step i { inline-size: .55rem; block-size: .55rem; border-radius: 50%;
  background: var(--brand-line); display: block;
  animation: aaa-blink 1.8s var(--ease) infinite;
  animation-delay: calc(var(--i) * 220ms); --anim-reduced: none; }
@keyframes aaa-blink { 0%, 100% { background: var(--brand-line); }
  50% { background: var(--brand); scale: 1.25; } }
</style>
"""

#: What the pipeline is doing, in the order it does it.
_STAGES: tuple[str, ...] = (
    "Checking your submission is complete and consistent",
    "Working out which EU AI Act articles apply to your system",
    "Reviewing your data governance and documentation",
    "Testing the model for accuracy, robustness and bias",
    "Assessing your governance, oversight and monitoring",
    "Writing your report and having it verified",
)


def render_running(system: str) -> None:
    """Render the waiting panel shown while the pipeline runs.

    :param system: The customer's system name, so the wait is about *their* audit.
    """
    steps = "".join(
        f'<div class="aaa-run-step" style="--i:{i}"><i aria-hidden="true"></i>'
        f"<span>{html.escape(stage)}</span></div>"
        for i, stage in enumerate(_STAGES))
    st.markdown(
        _RUNNING_CSS
        + '<div class="aaa-hero aaa-rise" style="margin-block-end:1.2rem">'
        '<div class="aaa-eyebrow">Audit in progress</div>'
        f'<h1 class="aaa-hero-title">We are auditing '
        f'{html.escape(system) if system else "your system"}.</h1>'
        '<p class="aaa-hero-sub">This takes a few minutes. Leave this tab open — '
        "we will show you the results the moment they are ready.</p></div>"
        f'<div class="aaa-card aaa-run aaa-rise" style="--i:1">{steps}</div>',
        unsafe_allow_html=True)
