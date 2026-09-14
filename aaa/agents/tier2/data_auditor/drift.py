"""Phase 2 drift step — training vs evaluation distribution (Art. 10 §2(g)).

``load_dataset`` returns whichever dataset it can find; drift needs *both*
frames, so this module resolves them independently and stays silent (a
not-computed result plus an observation finding) when only one exists.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.tools.drift_test import drift_test
from aaa.tools.findings import make_finding

logger = logging.getLogger(__name__)


def _load(store: Any, uri: str | None) -> Any:
    """Load a CSV artefact, returning ``None`` when unavailable.

    :param store: Evidence store used to resolve the URI.
    :type store: Any
    :param uri: Artefact URI, possibly ``None``.
    :type uri: str | None
    :returns: The dataframe, or ``None``.
    :rtype: Any
    """
    if not uri:
        return None
    try:
        return load_artifact_from_uri(uri, store, "csv")
    except ArtifactUnavailable as exc:
        logger.info("drift: dataset unavailable (%s).", exc)
        return None


def run_drift(store: Any, t01b: dict, decl: dict,
              findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the drift test and record a finding when the data has shifted.

    :param store: Evidence store used to resolve dataset URIs.
    :type store: Any
    :param t01b: Annex IV dossier.
    :type t01b: dict
    :param decl: Declaration summary (may carry ``stage_b``).
    :type decl: dict
    :param findings: Finding sink, appended in place.
    :type findings: list[dict[str, Any]]
    :returns: The ``drift_test`` result dict.
    :rtype: dict[str, Any]
    """
    stage_b = decl.get("stage_b") or t01b or {}
    ref = _load(store, t01b.get("training_dataset_uri")
                or stage_b.get("training_dataset_uri"))
    cur = _load(store, t01b.get("evaluation_dataset_uri")
                or stage_b.get("evaluation_dataset_uri"))
    result = drift_test(reference=ref, current=cur)
    if result["verdict"] == "FAIL":
        findings.append(make_finding(
            finding_id="P2-DRIFT",
            description=(f"Distribution shift between training and evaluation data: "
                         f"{', '.join(result['drifted_features'][:5])} "
                         f"(max PSI {result['max_psi']}, alert threshold 0.2)."),
            materiality="possibly_material", articles=["Art.10"], source_phase="P2",
            recommendation=("Re-check dataset provenance and split methodology; a shifted "
                            "evaluation set undermines the reported performance metrics."),
        ))
    elif not result["computed"]:
        findings.append(make_finding(
            finding_id="P2-DRIFT-NOTRUN",
            description=f"Drift could not be measured: {result['reason']}.",
            materiality="observation", articles=["Art.10"], source_phase="P2",
            recommendation="Supply both training and evaluation dataset URIs.",
        ))
    return result
