"""Selectboxes and multiselects, including the virtualised option list."""
from __future__ import annotations

from playwright.sync_api import Page

from scripts.wizard_fill.widgets.base import FillError, container, settle


def _selection(box) -> str | None:
    """The text of what a select or multiselect holds, or ``None`` when it holds nothing."""
    aria = box.locator("input").first.get_attribute("aria-label") or ""
    if not aria.startswith("Selected "):
        return None
    return aria[len("Selected "):].rsplit(". ", 1)[0]


def selected(page: Page, label: str) -> str | None:
    """What the selectbox labelled *label* currently holds.

    :param page: The page.
    :param label: The label its module renders.
    :returns: The chosen option, or ``None`` when nothing is chosen or no such select is shown.
    """
    box = container(page, "stSelectbox", label, wait=False)
    return _selection(box) if box.count() else None


def _holds(box, value: str) -> bool:
    """Whether a select or multiselect already holds *value*.

    Streamlit rewrites the control's ``aria-label`` to ``"Selected a, b. <label>"``
    once it holds a value, and that is the only place a *multi*select states its
    full selection in text. It cannot be split on commas — "4 — Employment,
    worker management and access to self-employment" is one option containing
    one — so the whole selection is matched as a substring instead.

    :param box: The widget container.
    :param value: The option to look for.
    :returns: ``True`` when it is already selected.
    """
    selection = _selection(box)
    return selection is not None and value in selection


def _choose(page: Page, control, value: str, label: str) -> None:
    """Filter an open option list to *value* and click it."""
    options = page.get_by_role("option")
    if options.filter(has_text=value).count() == 0:
        # Virtualised list: type to filter rather than scroll.
        control.type(value, delay=15)
        page.wait_for_timeout(400)
    exact = page.get_by_role("option", name=value, exact=True)
    target = exact.first if exact.count() else page.get_by_role(
        "option").filter(has_text=value).first
    if target.count() == 0:
        raise FillError(f"{label!r}: no option matching {value!r}")
    target.click()
    settle(page, 400)


def pick_select(page: Page, label: str, value: str) -> None:
    """Choose *value* in a Streamlit selectbox.

    :param page: The page.
    :param label: The label its module renders.
    :param value: The option to choose.
    :raises FillError: When the control or the option cannot be found.
    """
    box = container(page, "stSelectbox", label)
    if box.count() == 0:
        raise FillError(f"no selectbox labelled {label!r}")
    if _holds(box, value):
        return
    control = box.locator("input").first
    control.click()
    page.wait_for_timeout(250)
    _choose(page, control, value, label)


def pick_multi(page: Page, label: str, values: list[str]) -> None:
    """Choose every one of *values* in a Streamlit multiselect.

    :param page: The page.
    :param label: The label its module renders.
    :param values: Options to select, in order.
    :raises FillError: When the control or an option cannot be found.
    """
    for value in values:
        box = container(page, "stMultiSelect", label)
        if box.count() == 0:
            raise FillError(f"no multiselect labelled {label!r}")
        # Idempotent by design: step 3 seeds Annex III and territory from the
        # step-2 questionnaire, so several of these arrive already chosen — and a
        # chosen option is no longer in the dropdown to click.
        if _holds(box, value):
            continue
        control = box.locator("input").first
        control.click()
        page.wait_for_timeout(250)
        _choose(page, control, value, label)


__all__ = ["pick_multi", "pick_select", "selected"]
