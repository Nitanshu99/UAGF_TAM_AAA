"""The Playwright driver's labels must stay in step with the wizard source.

A UI driver fails quietly: a label is renamed, its locator matches nothing, the
field is left blank, and the run that follows is compared against a baseline it
no longer matches. This is the guard that turns that into a test failure rather
than a thinner audit — and it runs without a browser.
"""
from __future__ import annotations

import pytest

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.verify import verify_labels


def test_every_label_the_driver_targets_is_still_rendered() -> None:
    """Grep each label back out of the module that renders it."""
    assert verify_labels() == []


def test_the_stage_b_labels_come_from_the_render_spec() -> None:
    """Imported, never transcribed — a rename must reach the driver."""
    from aaa.ui.wizard.step3.stage_b.spec import _TEXT_FIELDS

    assert set(spec.STEP3_STAGE_B_TEXT.values()) == set(_TEXT_FIELDS)
    for field, (label, *_) in _TEXT_FIELDS.items():
        assert spec.STEP3_STAGE_B_TEXT[label] == field


def test_the_uploader_labels_come_from_the_upload_field_tables() -> None:
    """Same contract for the twelve document slots."""
    from aaa.ui.wizard.constants import DOC_UPLOAD_FIELDS, OPTIONAL_UPLOAD_FIELDS

    assert len(spec.UPLOADERS) == len(DOC_UPLOAD_FIELDS) + len(OPTIONAL_UPLOAD_FIELDS)
    for field in (*DOC_UPLOAD_FIELDS, *OPTIONAL_UPLOAD_FIELDS):
        assert spec.uploader_for(field) is not None


@pytest.mark.parametrize("field", ["risk_management_file_uri", "eu_doc_uri",
                                   "post_market_plan_uri"])
def test_the_annex_iv_uploaders_still_refuse_plain_text(field: str) -> None:
    """Why the driver swaps in a PDF sibling.

    The bundle names ``.txt`` for these three; the uploaders take
    ``pdf/doc/docx``. If that ever changes, the swap should stop happening —
    and this test is what says so.
    """
    assert "txt" not in spec.accepted_types(field)
    assert "pdf" in spec.accepted_types(field)


def test_question_4a_is_wired_to_the_composite_answer() -> None:
    """The checkbox that keeps Phases 3 and 4 in a composite system's plan."""
    assert spec.STEP2_CHECKBOXES["Yes — it ranks, scores, matches or classifies"] \
        == "has_ranking_component"


def test_the_fli_multiselects_map_onto_stage_a_fields() -> None:
    """Derived from the session keys the spec declares, not hand-written."""
    from aaa.ui.wizard.collect.stage.a import _STAGE_A_DEFAULTS

    for field in spec.FLI_MULTISELECTS.values():
        assert field in _STAGE_A_DEFAULTS, f"{field} is not a Stage A field"


def test_the_three_step_three_tabs_are_named_as_the_page_creates_them() -> None:
    """An inactive tab's panel is in the DOM but not fillable."""
    import pathlib

    body = pathlib.Path("aaa/ui/wizard/step3/__init__.py").read_text(encoding="utf-8")
    for name in spec.TABS.values():
        assert f'"{name}"' in body
