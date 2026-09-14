"""Step 3, *Documents, model & data*: the data-dictionary controls, filled after the uploads."""
from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.widgets import FillError, fill_text, pick_multi, pick_select


def step3_data_dictionary(page: Page, stage_b: dict) -> None:
    """Target column, sensitive columns, the favourable label and the ranking columns.

    Uploading a CSV swaps these widgets from free text to column-aware
    selects, so they are filled *after* the uploads and located by the labels the
    column-aware branch renders.

    :param page: The page.
    :param stage_b: The Stage B declaration.
    """
    block: dict[str, Any] = stage_b.get("data_dictionary") or {}
    target = str(block.get("target_column") or "")
    if target:
        try:
            pick_select(page, "Target column", target)
        except FillError:
            fill_text(page, "Target column", target)
    sensitive = [str(c) for c in block.get("sensitive_feature_columns") or []]
    if sensitive:
        try:
            pick_multi(page, "Sensitive feature columns", sensitive)
        except FillError:
            fill_text(page, "Sensitive feature columns (comma-separated)",
                      ", ".join(sensitive))
    if block.get("positive_label") is not None:
        fill_text(page, "Favourable / positive label", str(block["positive_label"]))
    ranking: dict[str, Any] = block.get("ranking") or {}
    for label, field in spec.RANKING_SELECTS.items():
        if ranking.get(field):
            try:
                pick_select(page, label, str(ranking[field]))
            except FillError:
                fill_text(page, label, str(ranking[field]))


__all__ = ["step3_data_dictionary"]
