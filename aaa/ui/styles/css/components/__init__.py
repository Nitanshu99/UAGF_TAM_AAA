"""Authored surfaces: the stepper, verdict hero, KPI tiles, pills, rows.

These are the parts of the page Streamlit has no widget for, rendered as
HTML through :func:`streamlit.markdown` and styled here.
"""

# One module per authored surface; the order here is the cascade order.
from __future__ import annotations

from aaa.ui.styles.css.components.hero import HERO
from aaa.ui.styles.css.components.kpi import KPI
from aaa.ui.styles.css.components.layout import LAYOUT
from aaa.ui.styles.css.components.pills import PILLS
from aaa.ui.styles.css.components.rows import ROWS
from aaa.ui.styles.css.components.stepper import STEPPER
from aaa.ui.styles.css.components.tabs import TABS

COMPONENTS = "".join((STEPPER, HERO, PILLS, KPI, ROWS, LAYOUT, TABS))

__all__ = ["COMPONENTS"]
