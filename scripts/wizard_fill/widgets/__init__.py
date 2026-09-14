"""Playwright helpers for the widget kinds Streamlit renders.

Three Streamlit behaviours decide the shape of everything here, and each cost a
session to find the hard way:

* A text widget commits on **blur or Enter**, not on change. Filling it and
  clicking the next control works; filling it and clicking *submit* does not,
  because the submit click is handled before the blur's rerun lands.
* A select's ``aria-label`` becomes ``"Selected x. <label>"`` once it holds a
  value, so ``get_by_label`` finds it before the first pick and loses it after.
  Widgets are located by their container's testid filtered on the label text.
* An option list is **virtualised**: a column past the first ten is simply not
  in the DOM. Typing into the control filters the list server-side first.

File inputs need none of this — ``set_input_files`` is a real browser file
selection, so React receives trusted events and the upload just happens.

``base`` holds the shared pieces; ``text``, ``select``, ``checkbox``, ``upload``
and ``nav`` hold one widget kind each.
"""
from scripts.wizard_fill.widgets.base import RERUN_MS, FillError, container, settle, wait_for_text
from scripts.wizard_fill.widgets.checkbox import set_checkbox
from scripts.wizard_fill.widgets.nav import click_button, expand, open_tab
from scripts.wizard_fill.widgets.select import pick_multi, pick_select, selected
from scripts.wizard_fill.widgets.text import fill_text
from scripts.wizard_fill.widgets.upload import upload

__all__ = ["RERUN_MS", "FillError", "click_button", "container", "expand", "fill_text",
           "open_tab", "pick_multi", "pick_select", "selected", "set_checkbox", "settle", "upload",
           "wait_for_text"]
