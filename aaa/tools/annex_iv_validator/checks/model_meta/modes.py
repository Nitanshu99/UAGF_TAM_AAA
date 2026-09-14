"""Access-mode-driven checks over the Stage B provenance fields."""
from __future__ import annotations

from typing import Any

from aaa.tools.annex_iv_validator.checks.model_meta.reference import check_adapter, check_reference
from aaa.tools.annex_iv_validator.checks.model_meta.rules import (
    FORMAT_FIELDS,
    MODE_FORBIDS,
    MODE_REQUIRES,
    REFERENCE_REQUIRES,
)
from aaa.tools.annex_iv_validator.checks.model_meta.status import (
    filled,
    make_absence_status,
    make_status,
)
from aaa.tools.annex_iv_validator.validationresult import ValidationResult


def declares_model(dossier: dict[str, Any]) -> bool:
    """True when the dossier offers a model in any form.

    :param dossier: Raw Stage B dossier.
    :returns: Whether an artefact, an access mode or a reference is declared.
    :rtype: bool
    """
    return any(filled(dossier.get(key)) for key in
               ("model_artifact_uri", "model_access_mode", "model_reference"))


def _check_unmoded_format(result: ValidationResult, dossier: dict[str, Any],
                          ref: dict[str, Any]) -> None:
    """Flag a format claim with no artefact and no reference behind it.

    Applicable only where a format is actually declared: the prohibition is on
    claiming one without backing, not on staying silent about it.
    """
    backed = bool(ref)
    for field in FORMAT_FIELDS:
        result.missing_conditional.append(make_absence_status(
            field, "declared without an artefact URI or a model_reference to back it",
            not backed and filled(dossier.get(field)), dossier.get(field)))


def check_access_mode(result: ValidationResult, dossier: dict[str, Any]) -> None:
    """Record every access-mode-conditional status on *result*.

    :param result: Validation result mutated in place.
    :param dossier: Raw Stage B dossier.
    """
    mode = str(dossier.get("model_access_mode") or "")
    ref = dossier.get("model_reference") or {}
    result.missing_conditional.append(make_status(
        "model_access_mode", "a model is supplied in any form (S6 hand-off)",
        declares_model(dossier), mode))
    if not mode and filled(dossier.get("model_artifact_uri")):
        # Dossiers predating the access-mode field: an uploaded artefact with
        # no declared mode *is* an artifact upload, so keep their old checks.
        mode = "artifact_upload"
    if not mode:
        _check_unmoded_format(result, dossier, ref)
        return
    for field in MODE_REQUIRES.get(mode, ()):
        result.missing_conditional.append(make_status(
            field, f"model_access_mode == '{mode}'", True, dossier.get(field)))
    for field in MODE_FORBIDS.get(mode, ()):
        result.missing_conditional.append(make_absence_status(
            field, f"model_access_mode == '{mode}' — no artefact exists to describe",
            True, dossier.get(field)))
    if mode in REFERENCE_REQUIRES:
        check_reference(result, mode, ref)
    if mode == "base_plus_adapter":
        check_adapter(result, ref)
