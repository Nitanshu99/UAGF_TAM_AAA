"""T09 records what the loaded model states about itself (T-20260913-065).

Case 03's model card left input shape, output shape and hyperparameters null
beside a loaded IsolationForest that carries all three, and the Verifier refused it.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from aaa.agents.tier2.model_validator.t09 import build_t09
from aaa.platform.evidence.contract import artefact_schema_errors
from aaa.tools.model_meta.introspect import model_facts

_X = np.random.default_rng(0).normal(size=(60, 4))
_Y = (_X[:, 0] > 0).astype(int)


def test_an_outlier_detector_states_its_shapes_and_settings() -> None:
    facts = model_facts(IsolationForest(n_estimators=25, random_state=0).fit(_X))
    assert facts["input_shape"] == "(n_samples, 4)"
    assert facts["output_shape"] == "(n_samples,) inlier/outlier label (+1 / -1)"
    assert facts["hyperparameters"]["n_estimators"] == 25
    assert facts["parameter_count"] is None, "a tree ensemble has no agreed parameter count"


def test_a_linear_pipeline_counts_its_coefficients() -> None:
    facts = model_facts(make_pipeline(StandardScaler(), LogisticRegression()).fit(_X, _Y))
    assert facts["parameter_count"] == 5 and facts["output_shape"].endswith("2 classes")
    assert facts["hyperparameters"]["C"] == 1.0


def test_without_a_model_nothing_is_claimed() -> None:
    assert set(model_facts(None).values()) == {None}


def test_the_model_card_carries_the_facts_and_validates() -> None:
    model = RandomForestRegressor(n_estimators=5, random_state=0).fit(_X, _X[:, 1])
    t09 = build_t09("eng", {}, {}, "tabular", {}, "2026-09-13T00:00:00Z", model=model)
    assert t09["architecture"]["input_shape"] == "(n_samples, 4)"
    assert t09["architecture"]["output_shape"] == "(n_samples,) predicted value"
    assert t09["training_regime"]["hyperparameters"]["n_estimators"] == 5
    assert artefact_schema_errors("T09_model_card", t09) == []


def test_an_outlier_detector_is_explained_locally_by_its_anomaly_score() -> None:
    """Case 03: LIME needed predict_proba, so the detector's T10 had no local explanations."""
    from aaa.agents.tier2.model_validator.context import EvalContext
    from aaa.agents.tier2.model_validator.explainability import run_explainability
    from aaa.agents.tier2.model_validator.t10 import build_t10

    ctx = EvalContext(t01a={}, t01b={}, stage_b={}, x_eval=_X, feature_names=["a", "b", "c", "d"],
                      model=IsolationForest(n_estimators=25, random_state=0).fit(_X))
    expl = run_explainability({}, "tabular", ctx)
    assert "lime" in expl.techniques and expl.local_expl
    assert expl.local_expl[0]["predicted_probability"] is None
    t10 = build_t10("eng", "tabular", expl, "2026-09-13T00:00:00Z")
    assert "anomaly score" in t10["interpretation"]
    assert all("explained_output" not in e for e in t10["local_explanations"])
    assert artefact_schema_errors("T10_explainability_report", t10) == []
