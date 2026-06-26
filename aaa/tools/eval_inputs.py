"""
aaa.tools.eval_inputs — Load + independently score a client's evaluation set.

Phase 3 (model validation) and Phase 4 (output fairness) both need the same thing:
the real model, the real evaluation set split into X / y, and the model's
predictions on it — plus the protected-attribute columns for fairness. Centralising
that here keeps the "trust nothing, recompute everything" contract in one place and
avoids two agents drifting apart.

Loading/validity findings (missing dataset, stub model, schema mismatch) are owned by
Phase 3 (``emit_load_findings=True``); Phase 4 consumes the result with
``emit_load_findings=False`` and only marks its own articles INSUFFICIENT_EVIDENCE
when the model could not be scored — so a single root cause is not double-reported.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.tools.data_dictionary import DataDictionary, resolve_data_dictionary
from aaa.tools.findings import make_finding

logger = logging.getLogger(__name__)


@dataclass
class ScoredEvaluation:
    """Result of loading + independently scoring an evaluation set."""

    model: Any = None
    X_eval: Any = None
    y_true: list[Any] | None = None
    y_pred: list[Any] | None = None
    y_proba: list[float] | None = None
    data_dict: DataDictionary | None = None
    sensitive_features: dict[str, list[Any]] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)

    @property
    def scored(self) -> bool:
        """True when an aligned (y_true, y_pred) pair is available."""
        return (
            self.y_true is not None and self.y_pred is not None
            and len(self.y_true) > 0 and len(self.y_pred) == len(self.y_true)
        )


def _predict(model: Any, X: Any) -> tuple[list[Any] | None, list[float] | None]:
    """Score X defensively; any failure → (None, None)."""
    try:
        y_pred = list(model.predict(X))
    except Exception as exc:  # noqa: BLE001
        logger.info("model.predict failed (%s); evaluation unscored.", exc)
        return None, None
    y_proba: list[float] | None = None
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)
            if hasattr(proba, "shape") and len(proba.shape) == 2 and proba.shape[1] == 2:
                y_proba = [float(row[1]) for row in proba]
        except Exception as exc:  # noqa: BLE001
            logger.info("model.predict_proba failed (%s); AUC unavailable.", exc)
    return y_pred, y_proba


def load_scored_evaluation(
    store: Any,
    stage_b: dict[str, Any],
    t01b: dict[str, Any] | None = None,
    *,
    emit_load_findings: bool = True,
    emit_datadict_findings: bool = True,
    source_phase: str = "P3",
) -> ScoredEvaluation:
    """Load the model + evaluation set and score it.

    Parameters
    ----------
    store:
        Evidence store used to resolve ``minio://`` URIs.
    stage_b / t01b:
        The Annex IV dossier (either or both carry the artefact URIs + data dictionary).
    emit_load_findings:
        Emit material findings for missing/unloadable/stub artefacts (Phase 3 owns these).
    emit_datadict_findings:
        Emit findings for inferred data-dictionary assumptions (Phase 3 owns these).
    source_phase:
        Tag for emitted findings.
    """
    stage_b = stage_b or {}
    t01b = t01b or {}
    result = ScoredEvaluation()

    def add(finding: dict[str, Any], *, load: bool = False, datadict: bool = False) -> None:
        if load and not emit_load_findings:
            return
        if datadict and not emit_datadict_findings:
            return
        result.findings.append(finding)

    model_uri = t01b.get("model_artifact_uri") or stage_b.get("model_artifact_uri")
    eval_uri = (
        t01b.get("evaluation_dataset_uri") or stage_b.get("evaluation_dataset_uri")
        or t01b.get("training_dataset_uri") or stage_b.get("training_dataset_uri")
    )

    # ── 1. Evaluation dataset ──────────────────────────────────────────────────
    df = None
    if eval_uri:
        try:
            df = load_artifact_from_uri(eval_uri, store, "csv")
        except ArtifactUnavailable as exc:
            add(make_finding(
                finding_id="P3-EVAL-LOAD",
                description=f"Evaluation dataset could not be loaded for independent "
                            f"verification: {exc.reason}.",
                materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
                recommendation="Provide a machine-readable evaluation set with a documented schema.",
            ), load=True)
    else:
        add(make_finding(
            finding_id="P3-EVAL-MISSING",
            description="No evaluation/training dataset URI supplied; model accuracy, "
                        "robustness and fairness could not be independently verified.",
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Supply an evaluation dataset URI in the Annex IV dossier.",
        ), load=True)

    if df is None or getattr(df, "empty", True):
        return result

    # ── 2. Split contract ──────────────────────────────────────────────────────
    dd = resolve_data_dictionary(stage_b or t01b, list(df.columns))
    result.data_dict = dd
    for note in dd.assumptions:
        add(make_finding(
            finding_id="P3-DATADICT",
            description=note,
            materiality="possibly_material" if not dd.target_explicit else "observation",
            articles=["Art.11", "Art.15"], source_phase=source_phase,
            recommendation="Declare a data dictionary (target/positive_label/sensitive columns).",
        ), datadict=True)
    if not dd.is_usable():
        return result

    result.X_eval = df[dd.feature_columns]
    result.y_true = list(df[dd.target_column])
    result.sensitive_features = {
        col: list(df[col]) for col in dd.sensitive_feature_columns if col in df.columns
    }

    # ── 3. Model ───────────────────────────────────────────────────────────────
    model = None
    if model_uri:
        try:
            model = load_artifact_from_uri(model_uri, store, "joblib")
        except ArtifactUnavailable as exc:
            add(make_finding(
                finding_id="P3-MODEL-LOAD",
                description=f"Model artefact could not be loaded; accuracy/robustness/fairness "
                            f"claims could not be independently verified: {exc.reason}.",
                materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
                recommendation="Provide the trained model artefact (joblib/pickle).",
            ), load=True)
    else:
        add(make_finding(
            finding_id="P3-MODEL-MISSING",
            description="No model artefact URI supplied; declared performance could not be "
                        "independently verified.",
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Supply a model_artifact_uri in the Annex IV dossier.",
        ), load=True)

    if model is None:
        return result
    if not callable(getattr(model, "predict", None)):
        add(make_finding(
            finding_id="P3-MODEL-INVALID",
            description=(
                f"Submitted model artefact is not an executable model "
                f"(loaded type={type(model).__name__}, no .predict method); the declared "
                "performance, robustness and fairness metrics are entirely unverifiable "
                "from this artefact."
            ),
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Submit the actual fitted model with a predict() interface.",
            evidence_uris=[model_uri] if model_uri else None,
        ), load=True)
        return result
    result.model = model

    # ── 4. Score ───────────────────────────────────────────────────────────────
    y_pred, y_proba = _predict(model, result.X_eval)
    if y_pred is None:
        add(make_finding(
            finding_id="P3-SCORE",
            description="Loaded model could not score the evaluation set (schema mismatch or "
                        "incompatible preprocessing); metrics could not be recomputed.",
            materiality="possibly_material", articles=["Art.15"], source_phase=source_phase,
            recommendation="Ship the model with its preprocessing pipeline matching the eval schema.",
        ), load=True)
    result.y_pred = y_pred
    result.y_proba = y_proba
    return result


__all__ = ["ScoredEvaluation", "load_scored_evaluation"]
