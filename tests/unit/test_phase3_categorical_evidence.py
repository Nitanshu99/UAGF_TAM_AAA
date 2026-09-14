"""Phase 3's tools on categorical features (fix 15, finding P3).

The case-01 post-fix run reached Art. 13 PASS and Art. 15 FAIL on nothing: SHAP,
LIME and the robustness probe each raised on the German Credit dataset's string
columns and degraded to a stub, and the agent could not tell. Two behaviours are
pinned here — the tools now receive the *model's* input matrix (categoricals
label-encoded, which is what the model is scored on), and when a tool does fall
back it says so loudly enough for the article to be marked unevidenced.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingClassifier

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.explainability import run_explainability
from aaa.agents.tier2.model_validator.t10 import build_t10
from aaa.agents.tier2.model_validator.unevidenced import flag_unevidenced
from aaa.agents.tier2.tools_run import tools_run
from aaa.tools.eval_inputs.model_utils import _build_model_matrix
from aaa.tools.robustness_probe import flip_categoricals, robustness_probe
from aaa.tools.robustness_probe.run_perturbation_probe import _run_perturbation_probe

_CATEGORIES = ["lt_0_DM", "ge_200_DM", "no_account"]
_FEATURES = ["checking_status", "age"]


class _LabelEncoder:
    """Stand-in for the fitted sklearn LabelEncoder saved in a model bundle."""

    def __init__(self, classes: list[str]):
        self.classes_ = np.array(classes)


@pytest.fixture(name="credit")
def _credit() -> tuple[GradientBoostingClassifier, pd.DataFrame, pd.DataFrame, list[int]]:
    """A categorical credit-scoring frame, its encoded matrix and a fitted model."""
    rng = np.random.default_rng(0)
    raw = pd.DataFrame({
        "checking_status": [_CATEGORIES[i % 3] for i in range(60)],
        "age": rng.integers(20, 70, 60).tolist(),
    })
    encoders = {"checking_status": _LabelEncoder(_CATEGORIES)}
    encoded = _build_model_matrix(raw, _FEATURES, encoders)
    y = [(1 if a > 45 else 0) for a in raw["age"]]
    model = GradientBoostingClassifier(random_state=0).fit(encoded, y)
    return model, raw, encoded, y


def _context(model, raw, encoded, y, *, encode: bool) -> EvalContext:
    """Build the Phase 3 context with or without the loader's encoded matrix."""
    return EvalContext(
        t01a={}, t01b={}, stage_b={}, model=model, x_eval=raw,
        x_model=encoded if encode else None, feature_names=_FEATURES, y_eval=y,
        categorical_features=["checking_status"] if encode else [])


# --------------------------------------------------------------------------
# The matrix the tools are handed
# --------------------------------------------------------------------------

def test_x_probe_prefers_the_model_matrix_over_the_raw_frame(credit):
    """Tools that run the model get the encoded matrix, not the client's strings."""
    ctx = _context(*credit, encode=True)
    assert ctx.x_probe is ctx.x_model
    assert not any(d == np.dtype("O") for d in ctx.x_probe.dtypes)


def test_x_probe_falls_back_to_x_eval_when_no_matrix_was_built(credit):
    """A directly injected dispatch has no loader matrix and is already model-ready."""
    ctx = _context(*credit, encode=False)
    assert ctx.x_probe is ctx.x_eval


def test_loader_result_carries_the_matrix_it_scores_with():
    """``X_model`` survives scoring — discarding it is what starved the tools."""
    from aaa.tools.eval_inputs.types import ScoredEvaluation
    result = ScoredEvaluation()
    assert result.X_model is None and not result.categorical_features


# --------------------------------------------------------------------------
# Explainability on categorical data
# --------------------------------------------------------------------------

def test_shap_and_lime_run_on_the_encoded_matrix(credit):
    """The tabular path reports real techniques, not variance/snapshot proxies."""
    expl = run_explainability({}, "tabular", _context(*credit, encode=True))
    assert expl.techniques == ["shap", "lime"]
    assert expl.global_expl["technique"] == "shap"
    assert expl.local_expl and not expl.degraded


def test_raw_categoricals_degrade_and_say_why(credit):
    """Without the encoded matrix neither tool can run — both declare it, neither reports numbers."""
    expl = run_explainability({}, "tabular", _context(*credit, encode=False))
    assert expl.techniques == ["none"]
    assert len(expl.degraded) == 2
    assert any("SHAP" in reason for reason in expl.degraded)
    assert any("LIME" in reason for reason in expl.degraded)


def test_no_proxy_numbers_stand_in_for_attributions(credit):
    """Column variances and raw feature values are not the model's attributions (T-20260913-061)."""
    expl = run_explainability({}, "tabular", _context(*credit, encode=False))
    assert expl.global_expl["feature_importance"] == [] and expl.local_expl == []
    assert expl.global_expl["technique"] == "none"


def test_without_a_model_nothing_is_attributed(credit):
    """No model, no attribution — the data alone once produced 'lime' contributions."""
    ctx = _context(*credit, encode=True)
    ctx.model = None
    expl = run_explainability({}, "tabular", ctx)
    assert expl.techniques == ["none"] and not expl.local_expl
    assert not expl.global_expl["feature_importance"]


def test_tools_that_could_not_run_are_not_listed_as_run(credit):
    """The inventory lists tools that produced output; the failures travel as reasons."""
    expl = run_explainability({}, "tabular", _context(*credit, encode=False))
    assert not {"shap_explain", "lime_explain"} & set(tools_run("P3", techniques=expl.techniques))


# --------------------------------------------------------------------------
# Declaring the failure into the artefact and the verdict
# --------------------------------------------------------------------------

def test_a_degraded_phase_marks_art13_unevidenced(credit):
    """Proxy attributions describe the data, so Art. 13 is unevidenced, not PASS."""
    ctx = _context(*credit, encode=False)
    expl = run_explainability({}, "tabular", ctx)
    flag_unevidenced(ctx, "tabular", expl, {"overall_robustness_verdict": "PASS"})
    assert "Art.13" in ctx.insufficient
    assert [f["finding_id"] for f in ctx.findings] == ["P3-EXPLAIN-UNEVIDENCED"]


def test_a_working_phase_leaves_art13_assessed(credit):
    """Model-based techniques evidence the article; no insufficiency is raised."""
    ctx = _context(*credit, encode=True)
    expl = run_explainability({}, "tabular", ctx)
    flag_unevidenced(ctx, "tabular", expl, {"overall_robustness_verdict": "PASS"})
    assert not ctx.insufficient and not ctx.findings


def test_an_unrun_probe_marks_art15_unevidenced(credit):
    """A probe that measured nothing cannot carry Art. 15 either way."""
    ctx = _context(*credit, encode=True)
    expl = run_explainability({}, "tabular", ctx)
    flag_unevidenced(ctx, "tabular", expl, {"overall_robustness_verdict": "NOT_TESTED"})
    assert "Art.15" in ctx.insufficient
    assert [f["finding_id"] for f in ctx.findings] == ["P3-ROBUST-UNEVIDENCED"]


def test_t10_records_the_degradation_without_leaking_diagnostics(credit):
    """The reason reaches ``skipped_reason``; the schema's closed blocks stay clean."""
    expl = run_explainability({}, "tabular", _context(*credit, encode=False))
    t10 = build_t10("eng-1", "tabular", expl, "2026-09-01T00:00:00Z")
    assert "could not be executed on the supplied model" in t10["skipped_reason"]
    assert "SHAP could not run" in t10["interpretation"]
    assert "degraded_reason" not in t10["global_explanation"]
    assert t10["global_explanation"]["feature_importance"] == []
    assert t10["local_explanations"] is None


def test_t10_is_quiet_when_nothing_degraded(credit):
    """No false alarm on the healthy path."""
    expl = run_explainability({}, "tabular", _context(*credit, encode=True))
    t10 = build_t10("eng-1", "tabular", expl, "2026-09-01T00:00:00Z")
    assert t10["skipped_reason"] is None
    assert "NOT model-based" not in t10["interpretation"]


# --------------------------------------------------------------------------
# The robustness probe
# --------------------------------------------------------------------------

def test_probe_scores_the_encoded_matrix(credit):
    """Clean prediction succeeds, so the probe reaches a verdict on measurement."""
    model, _raw, encoded, y = credit
    result = robustness_probe(model=model, X=encoded, y_true=y, modality="tabular",
                              categorical_features=["checking_status"])
    assert result["overall_robustness_verdict"] != "NOT_TESTED"
    assert result["clean_accuracy"] is not None
    assert len(result["probes"]) == 3


def test_probe_on_raw_categoricals_reports_not_tested(credit):
    """The old silent stub still reports honestly rather than inventing a verdict."""
    model, raw, _encoded, y = credit
    result = robustness_probe(model=model, X=raw, y_true=y, modality="tabular")
    assert result["overall_robustness_verdict"] == "NOT_TESTED"
    assert "clean prediction failed" in result["skipped_reason"]


def test_categorical_columns_are_flipped_not_noised(credit):
    """Encoded categories stay valid category indices under perturbation."""
    _model, _raw, encoded, _y = credit
    out = flip_categoricals(encoded, 0.5, ["checking_status"])
    assert set(out["checking_status"]) <= {0, 1, 2}
    assert (out["checking_status"] != encoded["checking_status"]).any()
    assert list(out["age"]) == list(encoded["age"])


def test_category_flip_is_deterministic(credit):
    """Same seed → same flips, so T11 re-runs reproduce."""
    _model, _raw, encoded, _y = credit
    first = flip_categoricals(encoded, 0.3, ["checking_status"], seed=11)
    second = flip_categoricals(encoded, 0.3, ["checking_status"], seed=11)
    assert list(first["checking_status"]) == list(second["checking_status"])


def test_a_failed_probe_records_nothing_rather_than_a_total_loss():
    """A raising probe used to report adversarial_accuracy 0.0 — a fabricated FAIL."""
    def _boom(_matrix):
        raise RuntimeError("predictor exploded")

    assert _run_perturbation_probe("tabular", _boom, pd.DataFrame({"a": [1.0]}),
                                   [1], 1.0, 0.1) is None


def test_unrunnable_probes_are_dropped_and_declared(credit):
    """Dropped probes cannot skew the verdict, and their absence is stated."""
    model, _raw, encoded, y = credit
    calls: list[int] = []

    def _flaky(X):
        calls.append(1)
        if len(calls) > 1:          # the clean pass succeeds, every probe fails
            raise RuntimeError("perturbed scoring exploded")
        return model.predict(X)

    result = robustness_probe(model=model, X=encoded, y_true=y, modality="tabular",
                              predict_fn=_flaky)
    assert result["probes"] == []
    assert result["min_adversarial_accuracy"] is None
    assert result["overall_robustness_verdict"] == "NOT_TESTED"
    assert "3 of 3 perturbation probes" in result["skipped_reason"]
