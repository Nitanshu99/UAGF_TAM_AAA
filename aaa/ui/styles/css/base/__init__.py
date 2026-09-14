"""Page shell, typography and the surface primitives every panel is built from.

Streamlit paints its own chrome, so the first job here is to take the canvas
back: the toolbar and the deploy button are the app owner's UI, not the
customer's, and a compliance audit that opens with someone else's "Deploy"
button does not read as a finished product.
"""

# One module per concern, in cascade order.
from __future__ import annotations

from aaa.ui.styles.css.base.data_tables import DATA_TABLES
from aaa.ui.styles.css.base.focus import FOCUS
from aaa.ui.styles.css.base.shell import SHELL
from aaa.ui.styles.css.base.surfaces import SURFACES
from aaa.ui.styles.css.base.typography import TYPOGRAPHY

#: The layer, in source order.
BASE = "".join((SHELL, TYPOGRAPHY, FOCUS, SURFACES, DATA_TABLES))

__all__ = ["BASE"]
