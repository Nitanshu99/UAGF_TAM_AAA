"""T12 says why output fairness was not tested, and never contradicts the dossier.

Case 06 recorded "No predictions or protected-attribute columns available" when
the phase had taken the generative short-circuit and the data dictionary declared
five protected attributes (T-20260913-011).
"""
from __future__ import annotations

from typing import Any, cast

import pytest

from aaa.agents.tier2.output_fairness import inputs as inputs_mod
from aaa.agents.tier2.output_fairness import skip_cause as cause
from aaa.agents.tier2.output_fairness.skip_text import skipped_reason
from aaa.agents.tier2.output_fairness.suite import run_fairness_suite
from aaa.agents.tier2.output_fairness.verdicts import apply_verdict_findings
from aaa.tools.eval_inputs import ScoredEvaluation

DECLARED = ["age_band", "sex", "nationality", "region", "first_language"]
STAGE_B = {"model_access_mode": "not_provided", "evaluation_dataset_uri": "minio://e/eval.csv",
           "data_dictionary": {"target_column": "advanced", "positive_label": 1,
                               "sensitive_feature_columns": DECLARED}}


def _scored(**fields: Any) -> ScoredEvaluation:
    result = ScoredEvaluation()
    for name, value in fields.items():
        setattr(result, name, value)
    return result


@pytest.mark.parametrize(("fields", "expected"), [
    ({}, cause.NO_EVALUATION_DATASET),
    ({"data_dict": cast(Any, object())}, cause.EVALUATION_SET_UNUSABLE),
    ({"data_dict": cast(Any, object()), "y_true": [1, 0]}, cause.MODEL_NOT_ACCESSIBLE),
    ({"y_true": [1, 0], "model": object()}, cause.MODEL_NOT_SCORABLE),
    ({"y_true": [1, 0], "y_pred": [1, 1], "model": object()}, cause.NO_PROTECTED_ATTRIBUTES),
    ({"y_true": [1, 0], "y_pred": [1, 1], "sensitive_features": {"sex": ["f", "m"]}}, None),
])
def test_the_cause_is_where_the_loader_stopped(fields: dict[str, Any], expected: str | None) -> None:
    """Read from what the loader populated, not assumed."""
    assert cause.diagnose(_scored(**fields)) == expected


@pytest.mark.parametrize("skip", [cause.GENERATIVE_ONLY, cause.NO_EVALUATION_DATASET,
                                  cause.EVALUATION_SET_UNUSABLE, cause.MODEL_NOT_ACCESSIBLE,
                                  cause.MODEL_NOT_SCORABLE, cause.NO_PROTECTED_ATTRIBUTES, None])
def test_every_reason_quotes_the_declared_attributes(skip: str | None) -> None:
    """No reason can say the columns are missing while listing the five declared."""
    reason = skipped_reason(skip, cause.declared_context(STAGE_B, {}))
    assert "Declared protected attributes: " + ", ".join(DECLARED) in reason
    assert "columns available" not in reason and "unavailable (see" not in reason


def test_a_case06_dossier_gets_the_model_access_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evaluation set loaded, no model: the access mode and the five attributes, end to end."""
    loaded = _scored(data_dict=cast(Any, object()), y_true=[1, 0, 1],
                     sensitive_features={name: ["x"] * 3 for name in DECLARED})
    monkeypatch.setattr(inputs_mod, "load_scored_evaluation", lambda *_a, **_k: loaded)
    inp = inputs_mod.resolve_inputs(cast(Any, None), {"stage_b": STAGE_B}, {}, "nlp")
    reason = apply_verdict_findings(inp, run_fairness_suite(inp)) or ""
    assert reason.startswith("Model predictions unavailable: model_access_mode=not_provided")
    assert inp.findings[0]["finding_id"] == "P4-NOT-TESTED"
    assert reason in inp.findings[0]["description"]


def test_a_generative_dispatch_says_so() -> None:
    """The short-circuit is named as the cause, not disguised as missing data."""
    inp = inputs_mod.resolve_inputs(cast(Any, None), {"stage_b": STAGE_B}, {}, "llm")
    assert inp.skip_cause == cause.GENERATIVE_ONLY
