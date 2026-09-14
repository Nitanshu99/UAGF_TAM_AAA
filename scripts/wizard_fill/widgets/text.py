"""Text inputs and textareas."""
from __future__ import annotations

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PWTimeout

from scripts.wizard_fill.widgets.base import RERUN_MS, FillError, settle


def fill_text(page: Page, label: str, value: str) -> None:
    """Fill a text input or textarea and commit it.

    :param page: The page.
    :param label: The widget's label, as its module renders it.
    :param value: The value to type.
    :raises FillError: When no such widget is on the page.
    """
    field = page.get_by_label(label, exact=True)
    try:
        field.first.wait_for(state="attached", timeout=RERUN_MS)
    except PWTimeout as exc:
        raise FillError(f"no text widget labelled {label!r}") from exc
    field.first.fill(value)
    # Blur commits; Enter would submit a single-line input but insert a newline
    # into a textarea, so blur is the one that is correct for both.
    field.first.blur()
    settle(page, 350)


__all__ = ["fill_text"]
