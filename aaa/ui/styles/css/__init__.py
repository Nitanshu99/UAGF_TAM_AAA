"""Assembled stylesheet for the auditor UI, in cascade-layer order."""
from __future__ import annotations

from aaa.ui.styles.css.base import BASE
from aaa.ui.styles.css.components import COMPONENTS
from aaa.ui.styles.css.motion import MOTION
from aaa.ui.styles.css.tokens import TOKENS
from aaa.ui.styles.css.widgets import WIDGETS

#: Concatenated in priority order: tokens define the vocabulary, base sets the
#: page, widgets tame Streamlit's chrome, components are the authored surfaces,
#: motion animates whatever the earlier layers put on screen.
STYLESHEET = "".join((TOKENS, BASE, WIDGETS, COMPONENTS, MOTION))

__all__ = ["STYLESHEET", "TOKENS", "BASE", "WIDGETS", "COMPONENTS", "MOTION"]
