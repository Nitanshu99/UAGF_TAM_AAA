"""Derive ``model_artifact_kind`` from the artefact URI when the caller left it blank.

Every entry point converges on Stage B — wizard, API and the mock-case runner —
so the fallback lives here rather than in each of them. The wizard asks the
customer directly and their answer arrives already set; this covers the paths
that have only a URI, and runs before validation so the derived value is stored
in T01b with everything else.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.model_meta import infer_artifact_kind


def derive_artifact_kind(stage_b_payload: dict[str, Any]) -> None:
    """Fill ``model_artifact_kind`` from ``model_artifact_uri`` when it is absent.

    A URI that yields no confident answer is left ``None`` rather than guessed:
    the hand-off then warns, which is the honest outcome (fix F7, finding S4).

    :param stage_b_payload: Raw Stage B payload, mutated in place.
    :type stage_b_payload: dict[str, Any]
    """
    uri = stage_b_payload.get("model_artifact_uri")
    if uri and stage_b_payload.get("model_artifact_kind") is None:
        kind = infer_artifact_kind(uri)
        if kind is not None:
            stage_b_payload["model_artifact_kind"] = kind
