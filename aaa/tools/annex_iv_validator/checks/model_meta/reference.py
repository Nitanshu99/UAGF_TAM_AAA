"""Checks over the ``model_reference`` block naming a model we do not host."""
from __future__ import annotations

from typing import Any

from aaa.tools.annex_iv_validator.checks.model_meta.rules import (
    MUTABLE_REVISIONS,
    REFERENCE_REQUIRES,
)
from aaa.tools.annex_iv_validator.checks.model_meta.status import (
    filled,
    make_absence_status,
    make_status,
)
from aaa.tools.annex_iv_validator.validationresult import ValidationResult


def _check_revision_pin(result: ValidationResult, mode: str, ref: dict[str, Any]) -> None:
    """Flag a revision naming a moving target rather than pinning a model."""
    revision = str(ref.get("revision") or "").strip().lower()
    result.missing_conditional.append(make_absence_status(
        "model_reference.revision",
        f"model_access_mode == '{mode}' — revision must be an immutable pin, "
        "not a branch name or 'latest'",
        True, revision if revision in MUTABLE_REVISIONS else ""))


def check_reference(result: ValidationResult, mode: str, ref: dict[str, Any]) -> None:
    """Record the ``model_reference`` keys required by *mode*.

    :param result: Validation result mutated in place.
    :param mode: The declared access mode.
    :param ref: The ``model_reference`` block, possibly empty.
    """
    for key in REFERENCE_REQUIRES.get(mode, ()):
        result.missing_conditional.append(make_status(
            f"model_reference.{key}", f"model_access_mode == '{mode}'", True, ref.get(key)))
    _check_revision_pin(result, mode, ref)


def check_adapter(result: ValidationResult, ref: dict[str, Any]) -> None:
    """Require exactly one adapter source under ``base_plus_adapter``.

    Both an uploaded adapter and a registry adapter would leave S6 without a
    single answer to which one it should load.

    :param result: Validation result mutated in place.
    :param ref: The ``model_reference`` block, possibly empty.
    """
    sources = [k for k in ("adapter_uri", "adapter_reference") if filled(ref.get(k))]
    result.missing_conditional.append(make_status(
        "model_reference.adapter_uri|adapter_reference",
        "model_access_mode == 'base_plus_adapter' — exactly one adapter source",
        True, "ok" if len(sources) == 1 else ""))
