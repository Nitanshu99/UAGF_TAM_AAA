"""Step 1–2 of the evaluation loader: dataset load + split contract."""
from __future__ import annotations

from typing import Any

from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.tools.data_dictionary import resolve_data_dictionary
from aaa.tools.eval_inputs.types import FindingSink
from aaa.tools.findings import make_finding


def load_eval_dataframe(store: Any, eval_uri: str | None, sink: FindingSink,
                        source_phase: str) -> Any:
    """Load the evaluation dataset, recording findings on failure.

    :returns: The dataframe, or ``None`` when unavailable.
    """
    if not eval_uri:
        sink.add(make_finding(
            finding_id="P3-EVAL-MISSING",
            description="No evaluation/training dataset URI supplied; model accuracy, "
                        "robustness and fairness could not be independently verified.",
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Supply an evaluation dataset URI in the Annex IV dossier.",
        ), load=True)
        return None
    try:
        return load_artifact_from_uri(eval_uri, store, "csv")
    except ArtifactUnavailable as exc:
        sink.add(make_finding(
            finding_id="P3-EVAL-LOAD",
            description=f"Evaluation dataset could not be loaded for independent "
                        f"verification: {exc.reason}.",
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Provide a machine-readable evaluation set with a documented schema.",
        ), load=True)
        return None


def apply_split_contract(df: Any, stage_b: dict, t01b: dict, sink: FindingSink,
                         source_phase: str) -> Any:
    """Resolve the data dictionary and split X / y / sensitive features.

    :returns: The resolved :class:`DataDictionary` (also stored on the result).
    """
    dd = resolve_data_dictionary(stage_b or t01b, list(df.columns))
    sink.result.data_dict = dd
    for note in dd.assumptions:
        sink.add(make_finding(
            finding_id="P3-DATADICT",
            description=note,
            materiality="possibly_material" if not dd.target_explicit else "observation",
            articles=["Art.11", "Art.15"], source_phase=source_phase,
            recommendation="Declare a data dictionary (target/positive_label/sensitive columns).",
        ), datadict=True)
    if not dd.is_usable():
        return dd
    sink.result.X_eval = df[dd.feature_columns]
    sink.result.y_true = list(df[dd.target_column])
    sink.result.sensitive_features = {
        col: list(df[col]) for col in dd.sensitive_feature_columns if col in df.columns
    }
    return dd
