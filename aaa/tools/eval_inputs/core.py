"""Orchestration of the load-and-score pipeline for phase agents."""
from __future__ import annotations

from typing import Any

from aaa.tools.eval_inputs.load.dataset import apply_split_contract, load_eval_dataframe
from aaa.tools.eval_inputs.load.declared_type import check_declared_model_type
from aaa.tools.eval_inputs.load.model import load_model
from aaa.tools.eval_inputs.model_matrix import build_model_matrix
from aaa.tools.eval_inputs.score_step import score_in_label_space
from aaa.tools.eval_inputs.scoring import _infer_task_type
from aaa.tools.eval_inputs.types import FindingSink, ScoredEvaluation
from aaa.tools.eval_inputs.uris import resolve_input_uris


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

    :param store: Evidence store used to resolve ``minio://`` URIs.
    :param stage_b: The Annex IV dossier (artefact URIs + data dictionary).
    :param t01b: Alternative dossier source (either or both may carry URIs).
    :param emit_load_findings: Emit findings for missing/unloadable artefacts
        (Phase 3 owns these).
    :param emit_datadict_findings: Emit findings for inferred data-dictionary
        assumptions (Phase 3 owns these).
    :param source_phase: Tag for emitted findings.
    :returns: The populated :class:`ScoredEvaluation`.
    """
    stage_b, t01b = stage_b or {}, t01b or {}
    sink = FindingSink(ScoredEvaluation(), emit_load_findings, emit_datadict_findings)
    result = sink.result

    model_uri, eval_uri, declared_format, access_mode = resolve_input_uris(stage_b, t01b)

    df = load_eval_dataframe(store, eval_uri, sink, source_phase)
    if df is None or getattr(df, "empty", True):
        return result
    if not apply_split_contract(df, stage_b, t01b, sink, source_phase).is_usable():
        return result

    model, encoders, feature_cols, _raw = load_model(
        store, model_uri, sink, source_phase, model_format=declared_format,
        access_mode=access_mode)
    if model is None:
        return result
    result.model = model
    result.task_type = _infer_task_type(model, result.y_true)
    check_declared_model_type(stage_b, t01b, model, sink, source_phase)

    X_model = build_model_matrix(result, df, feature_cols, encoders)
    score_in_label_space(sink, model, X_model, source_phase)
    return result
