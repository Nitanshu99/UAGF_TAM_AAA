"""Model-meta conditional checks for the Stage B dossier (S6 hand-off fields).

Missing fields are recorded as conditional-field findings on the
:class:`ValidationResult`; they do not invalidate intake, so legacy dossiers
continue to run while the gap is surfaced in the T01c report.

Checks used to hang off ``bool(model_artifact_uri)``, which made every one of
them *not applicable* whenever no artefact was uploaded. A dossier could
therefore declare ``model_format: huggingface`` with no artefact anywhere and
pass intake in silence. They now hang off ``model_access_mode``, so a claim
with nothing behind it is reachable by validation.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.state.model_vocab import SUPERVISED_TASK_TYPES
from aaa.tools.annex_iv_validator.checks.model_meta.modes import check_access_mode, declares_model
from aaa.tools.annex_iv_validator.checks.model_meta.status import make_status
from aaa.tools.annex_iv_validator.validationresult import ValidationResult

__all__ = ["check_model_meta"]


def check_model_meta(result: ValidationResult, dossier: dict[str, Any]) -> None:
    """Record S6 model-meta field statuses on *result* (findings, not failures).

    :param result: Validation result mutated in place.
    :type result: ValidationResult
    :param dossier: Raw Stage B dossier.
    :type dossier: dict[str, Any]
    """
    task_type = dossier.get("task_type")
    has_dataset = bool(dossier.get("training_dataset_uri")
                       or dossier.get("evaluation_dataset_uri"))
    result.missing_conditional.append(make_status(
        "task_type", "a model is supplied in any form (S6 hand-off)",
        declares_model(dossier), task_type))
    check_access_mode(result, dossier)
    result.missing_conditional.append(make_status(
        "target_column", "supervised task_type with a dataset uploaded",
        bool(task_type in SUPERVISED_TASK_TYPES and has_dataset),
        dossier.get("target_column")))
    result.missing_conditional.append(make_status(
        "positive_label", "task_type == 'binary_classification'",
        task_type == "binary_classification", dossier.get("positive_label")))
