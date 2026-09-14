"""Fill the wizard for case 06 — Mariposa-Edu GmbH — from its intake bundle.

The declaration is read from ``mock/06_mariposa_edu_gmbh/stage_a.json`` and
``stage_b.json``, so what the browser types is the same payload the CLI submits.
Nothing is transcribed by hand.

One module per wizard step: ``intro`` (steps 0 and 1), ``questionnaire`` (step 2),
``stage_a``, ``stage_b``, ``documents`` and ``data_dictionary`` (the three step-3
tabs); ``case`` reads
the bundle. :func:`fill` runs them in order.
"""
from __future__ import annotations

import pathlib

from playwright.sync_api import Page

from scripts.wizard_fill.mariposa.case import (
    CASE_DIR,
    FREE_FORM_DOCS,
    HEADINGS,
    annex_labels,
    load_case,
    uploadable,
)
from scripts.wizard_fill.mariposa.data_dictionary import step3_data_dictionary
from scripts.wizard_fill.mariposa.documents import step3_documents, step3_model_meta
from scripts.wizard_fill.mariposa.intro import step0, step1
from scripts.wizard_fill.mariposa.questionnaire import step2
from scripts.wizard_fill.mariposa.stage_a import step3_stage_a
from scripts.wizard_fill.mariposa.stage_b import step3_stage_b
from scripts.wizard_fill.widgets import settle


def fill(page: Page, url: str, case_dir: pathlib.Path = CASE_DIR,
         has_ranking: bool = True) -> list[str]:
    """Drive the whole wizard up to, but not including, the run button.

    :param page: A Playwright page.
    :param url: Where the wizard is served.
    :param case_dir: The intake bundle to fill from.
    :param has_ranking: The answer to question 4a, which keeps Phases 3 and 4
        in the plan for a composite system.
    :returns: Stage B fields whose document could not be attached.
    """
    stage_a, stage_b = load_case(case_dir)
    page.goto(url)
    settle(page, 1500)
    print("  step 0  identity")
    step0(page, stage_a)
    print("  step 1  free-form documents no Stage B field names")
    for rel in FREE_FORM_DOCS:
        print(f"      + {rel}")
    step1(page, case_dir)
    print("  step 2  questionnaire")
    step2(page, stage_a, has_ranking)
    print("  step 3  stage A")
    step3_stage_a(page, stage_a)
    print("  step 3  stage B")
    step3_stage_b(page, stage_b)
    print("  step 3  documents")
    unresolved = step3_documents(page, stage_b, case_dir)
    step3_model_meta(page, stage_b)
    step3_data_dictionary(page, stage_b)
    return unresolved


__all__ = ["CASE_DIR", "FREE_FORM_DOCS", "HEADINGS", "annex_labels", "fill", "load_case",
           "step0", "step1", "step2", "step3_data_dictionary", "step3_documents",
           "step3_model_meta", "step3_stage_a", "step3_stage_b", "uploadable"]
