"""Patching the model-artifact layout a declaration describes."""
from __future__ import annotations

from typing import Any

from aaa.tools.model_meta.corrections import COMPANY_IMMUTABLE


def _patch_layout(stage_b: dict[str, Any], company_key: str) -> bool:
    """Fill ``model_artifact_kind`` and the actionability columns (fix F7).

    The layout is *derived* from the artefact URI rather than tabulated per
    company, so a case whose upload changes shape cannot keep a stale
    declaration. A case with no artefact at all — LegalMind runs
    ``base_plus_adapter`` against a vendor-hosted model — is left ``None``:
    there is no artefact whose layout could be described.

    :param stage_b: Stage B dossier dict, mutated in place.
    :param company_key: Folder / company name matched against
        :data:`COMPANY_IMMUTABLE`.
    :returns: ``True`` when any field was filled.
    """
    from aaa.tools.model_meta.artifact_layout import infer_artifact_kind

    changed = False
    uri = stage_b.get("model_artifact_uri")
    if uri and stage_b.get("model_artifact_kind") is None:
        kind = infer_artifact_kind(uri)
        if kind is not None:
            stage_b["model_artifact_kind"] = kind
            changed = True
    immutable = next((v for k, v in COMPANY_IMMUTABLE.items() if k in company_key.lower()), None)
    if immutable and stage_b.get("immutable_feature_columns") is None:
        stage_b["immutable_feature_columns"] = list(immutable)
        changed = True
    return changed


__all__ = ["_patch_layout"]
