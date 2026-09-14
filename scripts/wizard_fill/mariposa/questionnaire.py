"""Step 2: the nine questions, answered from the declaration."""
from __future__ import annotations

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.mariposa.case import HEADINGS, annex_labels
from scripts.wizard_fill.widgets import (
    click_button,
    pick_multi,
    pick_select,
    set_checkbox,
    wait_for_text,
)


def step2(page: Page, stage_a: dict, has_ranking: bool) -> None:
    """Answer the checkboxes, selects and multiselects, then continue to step 3.

    :param page: The page.
    :param stage_a: The Stage A declaration.
    :param has_ranking: The answer to question 4a.
    """
    for label, answer in spec.STEP2_CHECKBOXES.items():
        want = has_ranking if answer == "has_ranking_component" else bool(
            stage_a.get(answer))
        set_checkbox(page, label, want)
    values: dict[str, list[str]] = {
        "entity_type": [str(v) for v in stage_a.get("entity_type") or []],
        "declared_annex_iii_sections": annex_labels(stage_a),
        "territorial_scope": [str(v) for v in stage_a.get("territorial_scope") or []],
    }
    for label, (field, _) in spec.STEP2_MULTISELECTS.items():
        pick_multi(page, label, values[field])
    for label, field in spec.STEP2_SELECTS.items():
        if stage_a.get(field):
            pick_select(page, label, str(stage_a[field]))
    click_button(page, spec.BUTTONS["step2_submit"])
    wait_for_text(page, HEADINGS[3])


__all__ = ["step2"]
