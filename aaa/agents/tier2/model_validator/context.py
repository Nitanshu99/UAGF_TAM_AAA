"""Shared data carriers passed between the Phase 3 pipeline steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalContext:
    """Model / evaluation artefacts resolved for the engagement.

    Direct injection from the dispatch (unit tests) wins; otherwise the
    artefacts are loaded from the Evidence Store via the declared URIs.
    """

    t01a: dict[str, Any]
    t01b: dict[str, Any]
    stage_b: dict[str, Any]
    model: Any = None
    x_eval: Any = None
    x_model: Any = None
    categorical_features: list[str] = field(default_factory=list)
    y_eval: Any = None
    y_pred: Any = None
    y_proba: Any = None
    feature_names: list[str] | None = None
    image_batch: Any = None
    image_ids: list[str] | None = None
    target_layer: Any = None
    eval_scored: bool = False
    #: The loader's inferred task and its label-space predictor (see ``eval_inputs.label_space``).
    task_type: str = "unknown"
    predict_fn: Any = None
    #: The target's positive class, from the data dictionary; ``None`` when unresolved.
    positive_label: Any = None
    #: ``ranking_metrics`` output when declared ranking metrics were attempted, else ``None``.
    ranking: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = field(default_factory=list)
    positives: list[dict[str, Any]] = field(default_factory=list)
    insufficient: set[str] = field(default_factory=set)

    @property
    def x_probe(self) -> Any:
        """The feature matrix to hand tools that must *run* the model.

        ``x_model`` when the loader built one (categoricals label-encoded into
        the model's own input space), else the raw ``x_eval`` — which is what a
        unit test or a direct dispatch injects, and is already model-ready.
        """
        return self.x_eval if self.x_model is None else self.x_model


@dataclass
class Explainability:
    """Explainability evidence gathered in step 3."""

    techniques: list[str]
    global_expl: dict[str, Any]
    local_expl: list[dict[str, Any]]
    visual_expl: list[dict[str, Any]]
    #: Why a technique fell back to a non-model proxy, one line per technique.
    #: Empty when every attempted technique actually executed. A tool that runs
    #: and fails soft is otherwise invisible to the model reading ``tool_outputs``.
    degraded: list[str] = field(default_factory=list)


@dataclass
class LlmSynthesis:
    """Outcome of the LLM synthesis call (step 5)."""

    summary: str | None
    prompt_note: str
    client_doc_hits: list[dict[str, Any]]
