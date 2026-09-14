"""Independent dataset loading for the Phase 2 audit."""
from __future__ import annotations

from typing import Any

from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.tools.findings import make_finding


def dataset_uri_of(t01b: dict, decl: dict) -> str | None:
    """The dataset Phase 2 examines: training set first, then evaluation set.

    One function, so the datasheet can say which dataset its counts describe.
    """
    return _dataset_of(t01b, decl)[1]


def dataset_role(t01b: dict, decl: dict) -> str | None:
    """Whether that dataset is the "training" or "evaluation" set, or ``None`` if unnamed."""
    return _dataset_of(t01b, decl)[0]


def _dataset_of(t01b: dict, decl: dict) -> tuple[str | None, str | None]:
    stage_b = decl.get("stage_b") or t01b or {}
    for role in ("training", "evaluation"):
        uri = t01b.get(f"{role}_dataset_uri") or stage_b.get(f"{role}_dataset_uri")
        if uri:
            return role, uri
    return None, decl.get("dataset_uri")


def load_dataset(store: Any, t01b: dict, decl: dict) -> tuple[Any, dict[str, Any] | None]:
    """Load the real training/evaluation dataset for independent analysis.

    A missing or unreadable dataset returns ``None`` plus a finding — never
    a silent empty frame that would let the data-governance checks pass on
    no evidence.

    :param store: Evidence store used to resolve URIs.
    :param t01b: Annex IV dossier.
    :param decl: Declaration summary (may carry ``stage_b`` / ``dataset_uri``).
    :returns: ``(dataframe_or_None, finding_or_None)``.
    """
    dataset_uri = dataset_uri_of(t01b, decl)
    if not dataset_uri:
        return None, make_finding(
            finding_id="P2-DATA-MISSING",
            description="No training/evaluation dataset URI supplied; data quality and "
                        "governance could not be independently verified.",
            materiality="possibly_material",
            articles=["Art.10"],
            source_phase="P2",
            recommendation="Supply a dataset URI in the Annex IV dossier.",
        )
    try:
        kind = "parquet" if dataset_uri.lower().endswith(".parquet") else "csv"
        return load_artifact_from_uri(dataset_uri, store, kind), None
    except ArtifactUnavailable as exc:
        return None, make_finding(
            finding_id="P2-DATA-LOAD",
            description=f"Training/evaluation dataset could not be loaded for "
                        f"independent verification: {exc.reason}.",
            materiality="possibly_material",
            articles=["Art.10"],
            source_phase="P2",
            recommendation="Provide a machine-readable dataset (CSV/Parquet).",
        )
