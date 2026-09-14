"""File uploaders."""
from __future__ import annotations

from playwright.sync_api import Page

from scripts.wizard_fill.widgets.base import FillError, container, settle


def upload(page: Page, label: str, path: str | list[str]) -> None:
    """Attach one or more files to the uploader under *label*.

    ``set_input_files`` is a real browser file selection, so React receives
    trusted events and the upload just happens.

    :param page: The page.
    :param label: The uploader's label, as ``DOC_UPLOAD_FIELDS`` declares it.
    :param path: Local file, or several for a multi-file uploader.
    :raises FillError: When no such uploader is on the page.
    """
    box = container(page, "stFileUploader", label)
    if box.count() == 0:
        raise FillError(f"no uploader labelled {label!r}")
    box.locator('input[type="file"]').first.set_input_files(path)
    settle(page, 1200 if isinstance(path, str) else 2500)


__all__ = ["upload"]
