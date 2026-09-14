"""Backfill logic for the S6 model-meta fields in existing fixtures.

Per-company vocabulary agreed with S6 (2026-07). Only ``None``/missing values
are ever filled — user data is never overwritten, which also makes the backfill
idempotent.

**Corrected 2026-09-06 (fix F9, findings S10/S11).** This docstring used to read
*"harbourlogistik's anomaly detector maps to binary_classification pending an
enum extension on the S6 side"*. The extension was never owed by S6: its field
sheet lists ``anomaly_detection`` among the accepted task types, and it was
:data:`aaa.platform.state.model_meta.TaskType` that could not express it. The
same narrowness cost two more declarations their meaning — RetailIQ's Chronos
transformer behind a random-forest wrapper declared bare ``sklearn``, and
LegalMind's LoRA adapter declared bare ``transformers`` — so a consumer loading
either by its declared framework gets the wrong object with no error. All three
are corrected here now that the vocabularies can hold them.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.model_meta.corrections import _DD_PROMOTE, COMPANY_META
from aaa.tools.model_meta.layout import _patch_layout


def patch_stage_b(stage_b: dict[str, Any], company_key: str) -> bool:
    """Fill the six S6 fields on *stage_b* in place, without overwriting.

    :param stage_b: Stage B dossier dict, mutated in place.
    :type stage_b: dict[str, Any]
    :param company_key: Folder / company name matched against ``COMPANY_META``.
    :type company_key: str
    :returns: ``True`` when any field was filled.
    :rtype: bool
    """
    changed = False
    meta = next((v for k, v in COMPANY_META.items() if k in company_key.lower()), None)
    if meta:
        for field, value in zip(("task_type", "model_format", "model_framework"), meta):
            if stage_b.get(field) is None:
                stage_b[field] = value
                changed = True
    dictionary = stage_b.get("data_dictionary") or {}
    for field in _DD_PROMOTE:
        value = dictionary.get(field)
        if stage_b.get(field) is None and value not in (None, "", []):
            stage_b[field] = value
            changed = True
    return _patch_layout(stage_b, company_key) or changed
