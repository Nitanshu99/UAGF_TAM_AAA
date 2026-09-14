"""Resolution of predictions, labels and protected attributes for Phase 4."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness import skip_cause
from aaa.agents.tier2.output_fairness.context import FairnessInputs
from aaa.platform.evidence import EvidenceStore
from aaa.tools.eval_inputs import load_scored_evaluation

_L_BRANCH = {"llm", "agentic", "gpai"}


def resolve_inputs(
    store: EvidenceStore,
    decl: dict[str, Any],
    t01b: dict[str, Any],
    modality: str,
) -> FairnessInputs:
    """Resolve the Phase 4 payload from the dispatch or the Evidence Store.

    Directly injected predictions (unit tests) win; otherwise the real model
    is independently scored on the evaluation set.  Load-level findings are
    owned by Phase 3 — only the scored result is consumed here.

    :param store: Evidence store used to load declared artefacts.
    :param decl: Declaration summary from the dispatch.
    :param t01b: T01b Annex IV dossier artefact (may be empty).
    :param modality: Normalised system modality.
    :returns: Populated :class:`FairnessInputs`.
    """
    inp = FairnessInputs(
        stage_b=decl.get("stage_b") or t01b or {},
        y_true=decl.get("y_true"), y_pred=decl.get("y_pred"),
        sensitive_features=decl.get("sensitive_features"),
        sensitive_map=decl.get("sensitive_features_map") or {},
        sensitive_feature_names=decl.get("sensitive_feature_names") or [],
        privileged_group=decl.get("privileged_group"),
        positive_label=decl.get("positive_label", 1),
        prediction_texts=decl.get("prediction_texts"),
        prediction_ids=decl.get("prediction_ids"),
        sampling_strategy=decl.get("sampling_strategy", "first_n"),
    )
    inp.skip_detail = skip_cause.declared_context(inp.stage_b, t01b)
    if inp.y_pred is not None:
        return inp
    if (modality or "tabular").lower() in _L_BRANCH:
        inp.skip_cause = skip_cause.GENERATIVE_ONLY
        return inp
    scored = load_scored_evaluation(
        store, inp.stage_b, t01b,
        emit_load_findings=False, emit_datadict_findings=False, source_phase="P4")
    inp.task_type = scored.task_type
    inp.skip_cause = skip_cause.diagnose(scored)
    if scored.scored:
        inp.y_true, inp.y_pred = scored.y_true, scored.y_pred
        inp.sensitive_map = scored.sensitive_features
        inp.sensitive_feature_names = list(inp.sensitive_map.keys())
        if scored.data_dict is not None:
            inp.positive_label = scored.data_dict.positive_label
    return inp
