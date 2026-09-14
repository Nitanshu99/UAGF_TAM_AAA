"""Moving around the form: buttons, step-3 tabs and expanders."""
from __future__ import annotations

from playwright.sync_api import Page

from scripts.wizard_fill.widgets.base import FillError, settle


def click_button(page: Page, text: str) -> None:
    """Click the button whose label contains *text*.

    :param page: The page.
    :param text: Substring of the button's label.
    :raises FillError: When no such button is on the page.
    """
    button = page.get_by_role("button").filter(has_text=text).first
    if button.count() == 0:
        raise FillError(f"no button matching {text!r}")
    button.click()
    settle(page)


def open_tab(page: Page, name: str) -> None:
    """Activate the step-3 tab called *name*.

    :param page: The page.
    :param name: The tab label, as ``st.tabs`` declares it.
    :raises FillError: When no such tab is on the page.
    """
    tab = page.get_by_role("tab", name=name, exact=True).first
    if tab.count() == 0:
        raise FillError(f"no tab named {name!r}")
    if tab.get_attribute("aria-selected") != "true":
        tab.click()
        settle(page, 500)


def expand(page: Page, text: str) -> None:
    """Open the expander whose summary contains *text*, if it is closed.

    :param page: The page.
    :param text: Substring of the expander's summary.
    """
    # `.last`, not `.first`: expanders nest, and an outer panel contains the
    # inner panel's summary text, so `.first` matches the parent and reports it
    # already open while the control you wanted stays collapsed.
    panel = page.locator('[data-testid="stExpander"]').filter(has_text=text).last
    if panel.count() == 0:
        return
    details = panel.locator("details").first
    summary = panel.locator("summary").first
    if summary.count() == 0:
        return
    # Streamlit renders a real <details>; `open` is the state, not aria-expanded.
    if details.count() and details.evaluate("el => el.open"):
        return
    summary.click()
    settle(page, 500)


__all__ = ["click_button", "expand", "open_tab"]
