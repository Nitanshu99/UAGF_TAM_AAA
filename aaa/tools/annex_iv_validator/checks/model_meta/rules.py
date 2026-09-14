"""Per-access-mode field requirements for the S6 hand-off.

The tables here replace the previous single gate on ``model_artifact_uri``.
That gate marked every check *not applicable* when no artefact was uploaded,
so a dossier could declare ``model_format: huggingface`` with no artefact
anywhere and pass intake in silence — the defect that sent S6 hunting for
weights that were never going to exist.
"""
from __future__ import annotations

#: access mode → dossier fields that must be declared under it.
MODE_REQUIRES: dict[str, tuple[str, ...]] = {
    "artifact_upload": ("model_artifact_uri", "model_format"),
    "registry_reference": ("model_format",),
    "base_plus_adapter": ("model_format",),
    "hosted_api": (),
    "not_provided": (),
}

#: access mode → dossier fields that must NOT be declared under it. A hosted
#: model has no artefact, so a serialisation format describes nothing.
MODE_FORBIDS: dict[str, tuple[str, ...]] = {
    "artifact_upload": (),
    "registry_reference": ("model_artifact_uri",),
    "base_plus_adapter": (),
    "hosted_api": ("model_format", "model_framework", "model_artifact_uri"),
    "not_provided": ("model_format", "model_framework", "model_artifact_uri"),
}

#: access mode → ``model_reference`` keys required under it.
REFERENCE_REQUIRES: dict[str, tuple[str, ...]] = {
    "registry_reference": ("provider", "model_id", "revision", "gated", "license"),
    "base_plus_adapter": ("provider", "model_id", "revision", "base_model_id",
                          "base_model_revision", "peft_type"),
    "hosted_api": ("provider", "model_id", "revision", "auth_type"),
}

#: Revision strings that name a moving target rather than pinning a model.
#: An audit pinned to one of these cannot name the weights it assessed.
MUTABLE_REVISIONS: frozenset[str] = frozenset(
    {"main", "master", "latest", "head", "dev", "develop", "stable", ""})

#: Fields that promise uploaded weights, used by the format-without-backing
#: check that closes the case-04 hole.
FORMAT_FIELDS: tuple[str, ...] = ("model_format", "model_framework")
