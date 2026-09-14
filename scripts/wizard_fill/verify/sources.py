"""Which rendering module must literally contain which of the driver's labels."""
from __future__ import annotations

from scripts.wizard_fill import form_spec as spec

#: Module → the labels that must appear literally in it.
SOURCES: dict[str, list[str]] = {
    "aaa/ui/wizard/step0/__init__.py": list(spec.STEP0_TEXT),
    "aaa/ui/wizard/step2/form.py": [
        "Yes, it processes personal data", "Yes, it processes special-category data",
        "Select all that apply", *spec.STEP2_SELECTS],
    "aaa/ui/wizard/step2/form2.py": [
        "Yes, this is a general-purpose AI model",
        "Yes — it ranks, scores, matches or classifies",
        "Yes, we elect voluntary third-party assessment",
        "Annex III categories", "Territory"],
    "aaa/ui/wizard/step3/stage_a/__init__.py": list(spec.STEP3_STAGE_A_TEXT),
    "aaa/ui/wizard/step3/stage_a/classification.py": [
        *spec.STEP3_SELECTS, spec.STEP3_ANNEX_LABEL],
    "aaa/ui/wizard/step3/stage_a/fli/__init__.py": list(spec.FLI_CHECKBOXES),
    "aaa/ui/wizard/step3/stage_a/contacts.py": [spec.CONTACTS_EXPANDER, *spec.STEP3_CONTACTS],
    "aaa/ui/wizard/step3/data_dict.py": [
        "Target column", "Sensitive feature columns", "Favourable / positive label"],
    "aaa/ui/wizard/step3/nav.py": [spec.BUTTONS["run"]],
    "aaa/ui/wizard/step1/__init__.py": [
        spec.BUTTONS["skip_uploads"], spec.BUTTONS["file_uploads"]],
    "aaa/ui/wizard/step1/widgets.py": list(spec.STEP1_UPLOADERS.values()),
    "aaa/ui/wizard/step0/__init__.py:buttons": [spec.BUTTONS["start"]],
}

#: Labels that live in dict literals the spec already imports, so re-grepping
#: them would only re-test Python's own import machinery.
IMPORTED = ("stage_b/spec.py", "constants.py", "fli/spec.py", "step3/ranking_columns.py")

#: The Annex IV core the audit gates on; an uploader must be declared for each.
CORE_UPLOAD_FIELDS = ("risk_management_file_uri", "eu_doc_uri", "post_market_plan_uri")

__all__ = ["CORE_UPLOAD_FIELDS", "IMPORTED", "SOURCES"]
