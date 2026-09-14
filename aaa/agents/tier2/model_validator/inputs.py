"""Resolution of model and evaluation artefacts for Phase 3."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.platform.evidence import EvidenceStore
from aaa.tools.eval_inputs import load_scored_evaluation


def build_eval_context(
    store: EvidenceStore,
    decl: dict[str, Any],
    t01a: dict[str, Any],
    t01b: dict[str, Any],
    modality: str,
) -> EvalContext:
    """Resolve the model / evaluation inputs for the engagement.

    :param store: Evidence store used to load declared artefacts.
    :param decl: Declaration summary from the dispatch.
    :param t01a: T01a triage artefact (may be empty).
    :param t01b: T01b Annex IV dossier artefact (may be empty).
    :param modality: Normalised system modality (``tabular``, ``cv``, ...).
    :returns: Populated :class:`EvalContext` including any loader findings
        and the Art. 15 insufficiency flags.
    """
    stage_b: dict[str, Any] = decl.get("stage_b") or t01b or {}
    ctx = EvalContext(
        t01a=t01a, t01b=t01b, stage_b=stage_b,
        model=decl.get("trained_model"), x_eval=decl.get("X_eval"),
        y_eval=decl.get("y_eval"), y_pred=decl.get("y_pred"),
        y_proba=decl.get("y_proba"), feature_names=decl.get("feature_names"),
        image_batch=decl.get("image_batch"), image_ids=decl.get("image_ids"),
        target_layer=decl.get("target_layer"), positive_label=decl.get("positive_label"),
    )
    model_uri = (t01b.get("model_artifact_uri")
                 or stage_b.get("model_artifact_uri")
                 or decl.get("model_artifact_uri"))
    eval_uri = (t01b.get("evaluation_dataset_uri")
                or stage_b.get("evaluation_dataset_uri")
                or t01b.get("training_dataset_uri")
                or stage_b.get("training_dataset_uri")
                or decl.get("evaluation_dataset_uri"))
    if modality != "cv" and ctx.model is None and (model_uri or eval_uri):
        scored = load_scored_evaluation(store, stage_b, t01b, source_phase="P3")
        ctx.model, ctx.x_eval = scored.model, scored.X_eval
        ctx.x_model, ctx.categorical_features = scored.X_model, scored.categorical_features
        ctx.y_eval, ctx.y_pred, ctx.y_proba = scored.y_true, scored.y_pred, scored.y_proba
        ctx.task_type, ctx.predict_fn = scored.task_type, scored.predict_fn
        if scored.data_dict:
            ctx.feature_names = ctx.feature_names or scored.data_dict.feature_columns
            ctx.positive_label = scored.data_dict.positive_label
        ctx.findings.extend(scored.findings)
    ctx.eval_scored = (
        ctx.y_eval is not None and ctx.y_pred is not None
        and len(ctx.y_eval) > 0 and len(ctx.y_pred) == len(ctx.y_eval)
    )
    if modality != "cv" and not ctx.eval_scored:
        ctx.insufficient.update({"Art.15", "Art.15§1"})
    return ctx
