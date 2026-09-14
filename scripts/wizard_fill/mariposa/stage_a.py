"""Step 3, *Your system*: identity, classification and the advanced FLI fields."""
from __future__ import annotations

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.mariposa.case import annex_labels
from scripts.wizard_fill.widgets import (
    expand,
    fill_text,
    open_tab,
    pick_multi,
    pick_select,
    set_checkbox,
)


def _fli_fields(page: Page, stage_a: dict) -> None:
    """The advanced compliance fields behind two nested expanders."""
    # Two nested expanders: `_render_about` wraps the flags, and
    # `render_fli_fields` opens its own inside that. Both must be open or the
    # FLI controls are in the DOM but not clickable.
    expand(page, "Advanced classification flags")
    expand(page, "Advanced compliance fields")
    for label, field in spec.FLI_CHECKBOXES.items():
        set_checkbox(page, label, bool(stage_a.get(field)))
    for label, field in spec.FLI_MULTISELECTS.items():
        pick_multi(page, label, [str(v) for v in stage_a.get(field) or []])
    label, field, _ = spec.FLI_EXCLUSION
    if stage_a.get(field):
        pick_select(page, label, str(stage_a[field]))


def _contacts(page: Page, contacts: dict) -> None:
    """The optional remediation owners, where the declaration names any."""
    if not any(contacts.get(role) for role in spec.STEP3_CONTACTS.values()):
        return
    expand(page, spec.CONTACTS_EXPANDER)
    for label, role in spec.STEP3_CONTACTS.items():
        if contacts.get(role):
            fill_text(page, label, str(contacts[role]))


def step3_stage_a(page: Page, stage_a: dict) -> None:
    """Fill the *Your system* tab from the Stage A declaration.

    :param page: The page.
    :param stage_a: The Stage A declaration.
    """
    open_tab(page, spec.TABS["stage_a"])
    for label, field in spec.STEP3_STAGE_A_TEXT.items():
        value = str(stage_a.get(field) or "")
        if value:
            fill_text(page, label, value)
    for label, field in spec.STEP3_SELECTS.items():
        value = str(stage_a.get(field) or "")
        if value:
            pick_select(page, label, value)
    pick_multi(page, spec.STEP3_ANNEX_LABEL, annex_labels(stage_a))
    _fli_fields(page, stage_a)
    _contacts(page, stage_a.get("organisation_contacts") or {})


__all__ = ["step3_stage_a"]
