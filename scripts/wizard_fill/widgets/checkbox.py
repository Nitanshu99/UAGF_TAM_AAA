"""Checkboxes."""
from __future__ import annotations

from playwright.sync_api import Page

from scripts.wizard_fill.widgets.base import FillError, container, settle


def set_checkbox(page: Page, label: str, want: bool) -> None:
    """Put a Streamlit checkbox into the wanted state.

    :param page: The page.
    :param label: The label its module renders.
    :param want: Desired state.
    :raises FillError: When no such checkbox is on the page.
    """
    holder = container(page, "stCheckbox", label)
    if holder.count() == 0:
        raise FillError(f"no checkbox labelled {label!r}")
    control = holder.locator('input[type="checkbox"]').first
    if control.is_checked() == want:
        return
    # The real input is visually hidden behind Streamlit's styled box, so it is
    # never "visible" to Playwright; the label is what a person actually clicks.
    holder.locator("label").first.click()
    settle(page, 350)
    if control.is_checked() != want:
        raise FillError(f"{label!r} would not toggle to {want}")


__all__ = ["set_checkbox"]
