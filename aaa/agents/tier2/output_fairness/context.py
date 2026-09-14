"""Shared data carriers passed between the Phase 4 pipeline steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Verdict bands ordered from best to worst; aggregation takes the worst band.
#: ``INSUFFICIENT_EVIDENCE`` — measured, but the interval cannot place the ratio on
#: either side of four-fifths — outranks an observation and yields only to a breach.
FAIRNESS_VERDICT_ORDER = ["NOT_TESTED", "PASS", "PASS_WITH_OBSERVATIONS",
                          "INSUFFICIENT_EVIDENCE", "FAIL"]

#: Maximum number of predictions sampled for the toxicity scan and T13 log.
TOXICITY_SAMPLE_CAP = 200


@dataclass
class FairnessInputs:
    """Predictions, labels and protected attributes resolved for Phase 4."""

    stage_b: dict[str, Any]
    y_true: Any = None
    y_pred: Any = None
    sensitive_features: Any = None
    sensitive_map: dict[str, list[Any]] = field(default_factory=dict)
    sensitive_feature_names: list[str] = field(default_factory=list)
    privileged_group: Any = None
    positive_label: Any = 1
    prediction_texts: Any = None
    prediction_ids: Any = None
    sampling_strategy: str = "first_n"
    task_type: str = "unknown"
    findings: list[dict[str, Any]] = field(default_factory=list)
    insufficient: set[str] = field(default_factory=set)
    #: Why the suite has nothing to test, from ``skip_cause``; ``None`` when it can run.
    skip_cause: str | None = None
    #: Declared attributes, access mode and evaluation URI the reason quotes.
    skip_detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class SuiteResult:
    """Outcome of the per-attribute fairness suite (steps 2–5)."""

    dp: dict[str, Any]
    eo: dict[str, Any]
    di: dict[str, Any]
    sg: dict[str, Any]
    overall_verdict: str
    sample_size: int | None
    per_attribute: list[dict[str, Any]]


@dataclass
class LlmSynthesis:
    """Outcome of the LLM synthesis call (step 8)."""

    summary: str | None
    prompt_note: str
