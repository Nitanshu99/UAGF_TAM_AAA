"""What every widget helper shares: the rerun budget, the error, the container locator."""
from __future__ import annotations

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PWTimeout

#: How long a Streamlit rerun is allowed to take before a step is called failed.
RERUN_MS = 15_000


class FillError(RuntimeError):
    """Raised when a widget the source declares is not on the page."""


def container(page: Page, testid: str, label: str, wait: bool = True):
    """The widget container whose label text contains *label*.

    :param page: The page.
    :param testid: Streamlit's container testid.
    :param label: Text that identifies this widget among its siblings.
    :param wait: Wait for it to attach rather than returning an empty locator.
    """
    found = page.locator(f'[data-testid="{testid}"]').filter(has_text=label).first
    if wait:
        try:
            found.wait_for(state="attached", timeout=RERUN_MS)
        except PWTimeout:
            pass
    return found


def settle(page: Page, ms: int = 900) -> None:
    """Wait for Streamlit's rerun to land.

    :param page: The page.
    :param ms: Quiet period to wait for after the network goes idle.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=RERUN_MS)
    except PWTimeout:
        pass
    page.wait_for_timeout(ms)


def wait_for_text(page: Page, marker: str, timeout_ms: int = RERUN_MS) -> None:
    """Block until *marker* is rendered.

    Streamlit runs over a websocket, so ``networkidle`` returns the instant the
    page has loaded and says nothing about whether the rerun has landed. Every
    step transition therefore waits for a heading the next step renders, taken
    from the module that renders it.

    :param page: The page.
    :param marker: Text the next screen must show.
    :param timeout_ms: How long to wait.
    :raises FillError: When the marker never appears.
    """
    try:
        page.get_by_text(marker, exact=False).first.wait_for(
            state="visible", timeout=timeout_ms)
    except PWTimeout as exc:
        raise FillError(f"expected {marker!r} after this step, never appeared") from exc
    page.wait_for_timeout(400)


__all__ = ["RERUN_MS", "FillError", "container", "settle", "wait_for_text"]
