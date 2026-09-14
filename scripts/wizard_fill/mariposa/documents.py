"""Step 3, *Documents, model & data*: the uploads and the model metadata."""
from __future__ import annotations

import pathlib

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.mariposa.case import uploadable
from scripts.wizard_fill.widgets import FillError, open_tab, pick_select, upload


def step3_documents(page: Page, stage_b: dict, case_dir: pathlib.Path) -> list[str]:
    """Attach every document the bundle names; returns the ones it could not.

    :param page: The page.
    :param stage_b: The Stage B declaration.
    :param case_dir: The intake bundle.
    :returns: Fields whose file could not be attached.
    """
    open_tab(page, spec.TABS["documents"])
    unresolved: list[str] = []
    for label, field in spec.UPLOADERS.items():
        value = stage_b.get(field)
        if not isinstance(value, str) or not value:
            continue
        path = uploadable(field, value, case_dir)
        if path is None:
            unresolved.append(field)
            continue
        upload(page, label, str(path))
    return unresolved


def step3_model_meta(page: Page, stage_b: dict) -> None:
    """Task type and how the model is made available.

    :param page: The page.
    :param stage_b: The Stage B declaration.
    """
    for label, (field, _) in spec.MODEL_META_SELECTS.items():
        value = str(stage_b.get(field) or "")
        if value:
            try:
                pick_select(page, label, value)
            except FillError as exc:
                print(f"      {label}: {exc}")


__all__ = ["step3_documents", "step3_model_meta"]
