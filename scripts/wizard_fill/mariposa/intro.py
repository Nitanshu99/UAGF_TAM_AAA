"""Steps 0 and 1: identity, then the free-form documents no Stage B field names."""
from __future__ import annotations

import pathlib

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.mariposa.case import FREE_FORM_DOCS, HEADINGS
from scripts.wizard_fill.widgets import click_button, fill_text, upload, wait_for_text


def step0(page: Page, stage_a: dict) -> None:
    """Company and system name, then start the engagement.

    :param page: The page.
    :param stage_a: The Stage A declaration.
    """
    for label, field in spec.STEP0_TEXT.items():
        fill_text(page, label, str(stage_a.get(field) or ""))
    click_button(page, spec.BUTTONS["start"])
    wait_for_text(page, HEADINGS[1])


def step1(page: Page, case_dir: pathlib.Path) -> list[str]:
    """Upload the documents no Stage B field names, then continue.

    :param page: The page.
    :param case_dir: The intake bundle.
    :returns: Paths that could not be attached.
    """
    paths = [str(case_dir / rel) for rel in FREE_FORM_DOCS
             if (case_dir / rel).is_file()]
    missing = [rel for rel in FREE_FORM_DOCS if not (case_dir / rel).is_file()]
    if paths:
        upload(page, spec.STEP1_UPLOADERS["documents"], paths)
    button = (spec.BUTTONS["file_uploads"] if paths
              else spec.BUTTONS["skip_uploads"])
    click_button(page, button)
    wait_for_text(page, HEADINGS[2])
    return missing


__all__ = ["step0", "step1"]
