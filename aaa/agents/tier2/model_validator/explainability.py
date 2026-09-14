"""Modality-routed explainability evidence collection (step 3)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.model_validator.context import EvalContext, Explainability
from aaa.tools.gradcam_explain import gradcam_explain
from aaa.tools.lime_explain import lime_explain
from aaa.tools.shap_explain import shap_explain
from aaa.tools.text_explain import token_contributions, token_importance


def run_explainability(
    decl: dict[str, Any],
    modality: str,
    ctx: EvalContext,
) -> Explainability:
    """Collect explainability evidence appropriate for the modality.

    ``cv`` systems get Grad-CAM saliency maps; ``nlp`` systems get
    |coef|-ranked token importances and exact per-instance token contributions
    when the model is a vectorizer + linear pipeline (SHAP/LIME otherwise); everything else gets SHAP global
    importances plus LIME local explanations. A technique that cannot run on
    the model reports nothing — never a model-free proxy — and says why.

    :param decl: Declaration summary (for optional ``class_names``).
    :param modality: Normalised system modality.
    :param ctx: Resolved model / evaluation inputs.
    :returns: :class:`Explainability` evidence; ``techniques == ["none"]``
        when no technique could be executed.  ``degraded`` names every
        technique that could not run on a supplied model, and why.
    """
    techniques: list[str] = []
    # sample_size None: nothing was explained, not an explanation over zero rows.
    global_expl: dict[str, Any] = {"technique": "none", "feature_importance": [],
                                   "sample_size": None, "tool": None}
    local_expl: list[dict[str, Any]] = []
    visual_expl: list[dict[str, Any]] = []
    degraded: list[str] = []
    if modality == "cv":
        visual_expl = gradcam_explain(model=ctx.model, images=ctx.image_batch,
                                      image_ids=ctx.image_ids,
                                      target_layer=ctx.target_layer, reasons=degraded)
        if visual_expl:
            techniques.append("gradcam")
    elif (modality == "nlp"
          and (nlp_expl := token_importance(model=ctx.model)).get("feature_importance")):
        global_expl = nlp_expl
        techniques.append("token_importance")
        # The same model explains each decision exactly (T-20260913-098).
        local_expl = token_contributions(model=ctx.model, X=ctx.x_probe, reasons=degraded)
        if local_expl:
            techniques.append("token_contribution")
    else:
        # ``x_probe``, not ``x_eval``: SHAP and LIME have to run the model, so
        # they need the matrix the model consumes, with its categoricals encoded.
        global_expl = shap_explain(model=ctx.model, X=ctx.x_probe,
                                   feature_names=ctx.feature_names)
        if global_expl.get("feature_importance"):
            techniques.append("shap")
        if global_expl.get("degraded_reason"):
            degraded.append(str(global_expl["degraded_reason"]))
        local_expl = lime_explain(model=ctx.model, X=ctx.x_probe,
                                  feature_names=ctx.feature_names,
                                  class_names=decl.get("class_names"), reasons=degraded)
        if local_expl:
            techniques.append("lime")
    return Explainability(techniques=techniques or ["none"], global_expl=global_expl,
                          local_expl=local_expl, visual_expl=visual_expl,
                          degraded=degraded)
