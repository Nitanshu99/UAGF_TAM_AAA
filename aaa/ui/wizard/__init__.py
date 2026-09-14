"""aaa.ui.wizard — modular implementation of the 5-step audit wizard.

Each wizard step lives in its own module; :mod:`aaa.ui.app` is the thin
Streamlit entry point that wires them together.

Step modules
------------
:mod:`aaa.ui.wizard.step0`  Start Engagement.
:mod:`aaa.ui.wizard.step1`  Upload Documents.
:mod:`aaa.ui.wizard.step2`  Quick Questions.
:mod:`aaa.ui.wizard.step3`  Review & Confirm (Stage A + Stage B forms).
:mod:`aaa.ui.wizard.step4`  Results dashboard.
"""
from __future__ import annotations

from aaa.ui.wizard.progress import render_progress
from aaa.ui.wizard.step0 import render_step_0
from aaa.ui.wizard.step1 import render_step_1
from aaa.ui.wizard.step2 import render_step_2
from aaa.ui.wizard.step3 import render_step_3
from aaa.ui.wizard.step4 import render_step_4

__all__ = [
    "render_progress",
    "render_step_0",
    "render_step_1",
    "render_step_2",
    "render_step_3",
    "render_step_4",
]
