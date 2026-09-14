"""
aaa.ui.app — EU AI Act conformity audit, customer front door (§10, §11).

Two surfaces, one session:

**The wizard** (``st.session_state["step"]``), which is what a customer sees.

  0. Get started — company and system name; the engagement id is derived.
  1. Your documents — technical docs, model artefacts, datasets.
  2. A few questions — 8 things the agent cannot read out of a document.
  3. Check the details — review and edit the pre-filled Stage A + Stage B form.
  4. Your results — a dashboard: verdict, KPIs, two PDFs, article breakdown,
     and what to do next. No artefact ids, no JSON, no T-numbers.

**The admin console** (``st.session_state["view"] == "admin"``), reached from a
button on that dashboard, which is where everything addressed to an auditor
lives: HITL review packets, T17/T18, run integrity, the raw AuditState.

Run::

    CGSA_FIXTURE_DIR=scripts/fixtures/cgsa \\
    streamlit run aaa/ui/app.py

The step implementations live in :mod:`aaa.ui.wizard`, the console in
:mod:`aaa.ui.admin`, and the design system in :mod:`aaa.ui.styles`; this module
only bootstraps the environment and routes between the two views.
"""
from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ``streamlit run aaa/ui/app.py`` executes this file as a script with the repo
# root off ``sys.path``, and the wizard modules read ``.env`` at import time —
# so the path fix and the dotenv load have to precede the imports below.
# pylint: disable=wrong-import-position,ungrouped-imports
from aaa.platform.env_bootstrap import load_repo_dotenv  # noqa: E402

load_repo_dotenv(REPO_ROOT)

import streamlit as st  # noqa: E402

from aaa.ui.wizard import (  # noqa: E402
    render_progress,
    render_step_0,
    render_step_1,
    render_step_2,
    render_step_3,
    render_step_4,
)

# Re-exported for backwards compatibility (tests + external callers).
from aaa.ui.wizard.collect import collect_stage_a as _collect_stage_a  # noqa: E402,F401
from aaa.ui.wizard.collect import collect_stage_b as _collect_stage_b  # noqa: E402,F401
from aaa.ui.wizard.loaders import store_uploaded_file as _store_uploaded_file  # noqa: E402,F401
from aaa.ui.wizard.parsing import normalise_version as _normalise_version  # noqa: E402,F401
from aaa.ui.wizard.parsing import parse_stage_b_metrics as _parse_stage_b_metrics  # noqa: E402,F401

_STEPS = {0: render_step_0, 1: render_step_1, 2: render_step_2,
          3: render_step_3, 4: render_step_4}


def _render_view() -> None:
    """Render whichever of the two surfaces the session is currently on.

    The customer sees the wizard and, at the end, a dashboard. The admin
    console — HITL packets, T17/T18, the raw AuditState — is a separate view
    reached from a button on that dashboard, because none of it is addressed
    to the customer and all of it was previously in their way.
    """
    if st.session_state.get("view") == "admin":
        from aaa.ui.admin import render_admin
        render_admin()
        return
    step = st.session_state["step"]
    if step < 4:
        render_progress(step)
    _STEPS.get(step, render_step_0)()


def main() -> None:
    """Configure the page, inject the theme, and render the active view."""
    st.set_page_config(
        page_title="EU AI Act Conformity Audit",
        page_icon="\u2713",
        layout="wide",
    )
    from aaa.ui import styles
    styles.inject_theme()
    if "step" not in st.session_state:
        st.session_state["step"] = 0
    _render_view()


if __name__ == "__main__":
    main()
