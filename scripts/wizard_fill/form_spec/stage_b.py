"""Step 3, *The dossier* and *Documents, model & data*: text, uploaders and model metadata."""
from __future__ import annotations

from typing import Any

from aaa.platform.state.model_vocab import TASK_TYPES
from aaa.ui.wizard.constants import DOC_UPLOAD_FIELDS, OPTIONAL_UPLOAD_FIELDS
from aaa.ui.wizard.step3.ranking_columns import RANKING_FIELDS
from aaa.ui.wizard.step3.stage_b.spec import _TEXT_FIELDS

#: Step 3 Stage B — label → field, taken straight from the render spec.
STEP3_STAGE_B_TEXT = {label: field for field, (label, *_) in _TEXT_FIELDS.items()}

#: Step 3 Stage B — the raw-text widgets the spec does not cover, each of which
#: the collector parses out of a single box (see ``collect_stage_b``).
STEP3_STAGE_B_RAW = {
    "Performance metrics (JSON)": "accuracy_metrics",
    "Significant changes log (one change per line)": "lifecycle_change_log",
    "Harmonised standards applied (comma-separated)": "harmonised_standards",
    "Other standards applied (comma-separated)": "other_standards",
    "Tool inventory (comma-separated)": "tool_inventory",
}

#: Step 3 — uploader label → the Stage B URI field it fills, in render order.
UPLOADERS: dict[str, str] = {
    label: field
    for field, (label, *_) in {**DOC_UPLOAD_FIELDS, **OPTIONAL_UPLOAD_FIELDS}.items()
}

#: Step 3 — model-provenance and task selectboxes.
MODEL_META_SELECTS = {
    "Task type": ("task_type", list(TASK_TYPES)),
    "How is the model made available?": ("model_access_mode", None),
}

#: Step 3 data dictionary — ranking-column label → its ``data_dictionary.ranking`` key.
RANKING_SELECTS = {label: field for field, (label, *_) in RANKING_FIELDS.items()}


def uploader_for(field: str) -> str | None:
    """The uploader label that fills a given Stage B field.

    :param field: A Stage B URI field name.
    :returns: The label rendered above its uploader, or ``None``.
    """
    for label, mapped in UPLOADERS.items():
        if mapped == field:
            return label
    return None


def accepted_types(field: str) -> list[str]:
    """File extensions a given uploader accepts.

    The three Annex IV documents accept ``pdf/doc/docx`` only, so a bundle that
    ships ``.txt`` needs its PDF sibling — a mismatch the driver should report
    rather than silently skip.

    :param field: A Stage B URI field name.
    :returns: Lower-case extensions, empty when the field has no uploader.
    """
    spec: Any = {**DOC_UPLOAD_FIELDS, **OPTIONAL_UPLOAD_FIELDS}.get(field)
    return [str(t).lower() for t in spec[2]] if spec else []


__all__ = ["MODEL_META_SELECTS", "RANKING_SELECTS", "STEP3_STAGE_B_RAW", "STEP3_STAGE_B_TEXT", "UPLOADERS",
           "accepted_types", "uploader_for"]
