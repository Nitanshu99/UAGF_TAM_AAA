"""The declared model_type must be reconciled against the artefact loaded.

Regression test for the documentation-accuracy gap: every Phase 3 check runs
on the loaded estimator and none of them look back at what the dossier claimed
it was, so the FinClear fixture declared ``gradient_boosted_trees_xgboost_v2``
for a scikit-learn ``GradientBoostingClassifier`` — with xgboost not installed
— and passed the whole pipeline silently until an integrator tried to load it.
"""
from __future__ import annotations

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from aaa.tools.eval_inputs.load.declared_type import check_declared_model_type
from aaa.tools.eval_inputs.types import FindingSink, ScoredEvaluation


def _findings(declared, model, *, emit_load: bool = True) -> list[dict]:
    """Run the check over one (declared, artefact) pair and return its findings."""
    sink = FindingSink(ScoredEvaluation(), emit_load=emit_load)
    check_declared_model_type({"model_type": declared}, {}, model, sink, "P3")
    return sink.result.findings


def test_declared_xgboost_against_an_sklearn_artefact_is_flagged():
    """The FinClear defect: a library claim the artefact contradicts."""
    findings = _findings("gradient_boosted_trees_xgboost_v2", GradientBoostingClassifier())
    assert len(findings) == 1
    finding = findings[0]
    assert finding["finding_id"] == "P3-MODEL-TYPE-MISMATCH"
    assert finding["eu_ai_act_articles"] == ["Art.11", "Art.15"]
    assert finding["declared"] == "gradient_boosted_trees_xgboost_v2"
    assert finding["observed"] == "sklearn.ensemble._gb.GradientBoostingClassifier"
    # Both sides must be legible in the narrative, not only in the metadata.
    assert "xgboost" in finding["description"]
    assert "GradientBoostingClassifier" in finding["description"]


def test_t01b_model_type_wins_over_stage_b():
    """T01b is the authoritative dossier everywhere else in the loader."""
    sink = FindingSink(ScoredEvaluation())
    check_declared_model_type({"model_type": "sklearn_gbt"}, {"model_type": "xgboost_v2"},
                              GradientBoostingClassifier(), sink, "P3")
    assert [f["declared"] for f in sink.result.findings] == ["xgboost_v2"]


def test_declared_sklearn_against_an_sklearn_artefact_is_clean():
    """The corrected FinClear declaration must not flag."""
    assert not _findings("sklearn_gradient_boosting_classifier_v2.1",
                         GradientBoostingClassifier())


def test_a_pipeline_wrapping_the_declared_estimator_is_clean():
    """mock/05's shape: the real estimator is a nested step, not the top class.

    Guards the decision to compare implementation library only — a family
    check would flag this correct artefact, because the loaded class is
    ``Pipeline`` and the ``LogisticRegression`` sits inside it.
    """
    pipeline = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression())])
    assert not _findings("tfidf_logistic_regression_sklearn_v1.2", pipeline)


def test_a_declaration_naming_no_library_is_clean():
    """mock/03's shape: an architecture name commits to no package."""
    assert not _findings("isolation_forest_anomaly_detection", GradientBoostingClassifier())
    assert not _findings("time_series_transformer_chronos_tiny_rf_wrapper",
                         GradientBoostingClassifier())


def test_one_satisfied_library_is_enough_when_several_are_named():
    """A wrapper declaration naming both libraries is not a false claim."""
    assert not _findings("xgboost_sklearn_wrapper", GradientBoostingClassifier())


def test_missing_declaration_or_missing_model_is_clean():
    """Absent inputs are other findings' business (P3-MODEL-MISSING), not this one."""
    assert not _findings(None, GradientBoostingClassifier())
    assert not _findings("", GradientBoostingClassifier())
    assert not _findings("gradient_boosted_trees_xgboost_v2", None)


def test_the_finding_is_suppressed_with_the_other_load_findings():
    """Phase 3 owns load findings; callers that opt out must not see this one."""
    assert not _findings("gradient_boosted_trees_xgboost_v2", GradientBoostingClassifier(),
                         emit_load=False)
