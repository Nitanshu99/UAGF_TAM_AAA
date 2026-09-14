"""Input-URI and format resolution for the evaluation loader.

Both the T01b artefact and the raw stage_b dossier may carry the artefact
URIs and the declared model format; T01b wins when both are present.
"""
from __future__ import annotations

from typing import Any


def resolve_input_uris(
    stage_b: dict[str, Any], t01b: dict[str, Any],
) -> tuple[str | None, str | None, str | None, str | None]:
    """Resolve the model URI, evaluation-set URI, format, and access mode.

    :param stage_b: The raw Stage B Annex IV dossier.
    :type stage_b: dict[str, Any]
    :param t01b: The stored T01b artefact (may duplicate stage_b).
    :type t01b: dict[str, Any]
    :returns: ``(model_uri, eval_uri, model_format, access_mode)`` — evaluation
        set falls back to the training set; any element may be ``None``.
    :rtype: tuple[str | None, str | None, str | None, str | None]
    """
    model_uri = t01b.get("model_artifact_uri") or stage_b.get("model_artifact_uri")
    eval_uri = (
        t01b.get("evaluation_dataset_uri") or stage_b.get("evaluation_dataset_uri")
        or t01b.get("training_dataset_uri") or stage_b.get("training_dataset_uri")
    )
    model_format = t01b.get("model_format") or stage_b.get("model_format")
    access_mode = t01b.get("model_access_mode") or stage_b.get("model_access_mode")
    return model_uri, eval_uri, model_format, access_mode
