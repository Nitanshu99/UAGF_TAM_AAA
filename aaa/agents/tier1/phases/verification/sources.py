"""The URIs a Verifier review may link an artefact to: the dispatch's plus the phase's inputs.

Case 03 (2026-09-13): T10 and T11 were marked down for "evidence linkage" because
the review listed only the intake artefacts; the model and datasets Phase 3
actually computed SHAP values and probe results from travelled in the
declaration summary and never reached the list the Verifier trusts.
"""
from __future__ import annotations

from typing import Any

#: Declared input artefacts a phase computes from.
INPUT_KEYS = ("model_artifact_uri", "evaluation_dataset_uri", "training_dataset_uri",
              "golden_set_uri")


def review_evidence_uris(dispatch: Any) -> list[str]:
    """The dispatch's evidence URIs followed by its declared input artefacts, de-duplicated.

    :param dispatch: The phase dispatch (``evidence_uris``, ``declaration_summary``).
    """
    summary = dict(dispatch.get("declaration_summary", {}) or {})
    dossier = summary.get("stage_b") or {}
    inputs = [summary.get(key) or dossier.get(key) for key in INPUT_KEYS]
    uris = [*(dispatch.get("evidence_uris", []) or []), *inputs]
    return list(dict.fromkeys(str(u) for u in uris if u))
