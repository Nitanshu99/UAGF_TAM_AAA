"""Restyle Streamlit's own widgets so they belong to the same design language.

Streamlit renders real ``<button>`` / ``<input>`` / ``<details>`` elements, so
these are ordinary style overrides rather than replacements — the keyboard
handling, the accessible names and the file-picker semantics all stay native
(§"Theming browser-generated UI": verify the built-in UI cannot be customised
enough *before* re-creating it; here it can).
"""

# One module per widget family, in the order the layer declares them.
from __future__ import annotations

from aaa.ui.styles.css.widgets.alerts import ALERTS
from aaa.ui.styles.css.widgets.button_variants import BUTTON_VARIANTS
from aaa.ui.styles.css.widgets.buttons import BUTTONS_BASE
from aaa.ui.styles.css.widgets.expanders import EXPANDERS
from aaa.ui.styles.css.widgets.file_uploader import FILE_UPLOADER
from aaa.ui.styles.css.widgets.keyed_containers_used_as_cards import KEYED_CONTAINERS_USED_AS_CARDS
from aaa.ui.styles.css.widgets.misc import MISC
from aaa.ui.styles.css.widgets.text_fields import TEXT_FIELDS

#: The layer, in source order.
WIDGETS = "".join((BUTTONS_BASE, BUTTON_VARIANTS, TEXT_FIELDS, FILE_UPLOADER, EXPANDERS, ALERTS, KEYED_CONTAINERS_USED_AS_CARDS, MISC))

__all__ = ["WIDGETS"]
