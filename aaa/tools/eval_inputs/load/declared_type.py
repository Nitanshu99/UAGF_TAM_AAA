"""Step 4 of the evaluation loader: declared-vs-actual model identity.

Annex IV §1 requires the technical documentation to describe the system as it
actually is, but nothing downstream ever re-reads the estimator's own identity:
the accuracy, robustness and fairness checks all run *on* the loaded artefact
and never look back at what the dossier claimed it was. A dossier naming one
implementation library while the artefact ships another therefore passes every
existing check untouched — which is exactly how the FinClear fixture came to
declare ``gradient_boosted_trees_xgboost_v2`` for a scikit-learn
``GradientBoostingClassifier``, with xgboost not even installed.

The comparison is deliberately restricted to the implementation *library*.
Estimator family is not checked: a declared ``tfidf_logistic_regression``
legitimately ships as a :class:`sklearn.pipeline.Pipeline` whose
``LogisticRegression`` sits in a nested step, and a family check would flag
that correct artefact. A library claim has no such indirection — either the
loaded class comes from the named package or the documentation is wrong.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.eval_inputs.types import FindingSink
from aaa.tools.findings import make_finding

#: Library token appearing in a declared ``model_type`` → module-path fragments
#: that satisfy it. Architecture names (``transformer``, ``chronos``) are
#: deliberately absent: they describe a model's shape, not the package that
#: implements it, and a wrapper around one is not a false claim.
_LIBRARIES: dict[str, tuple[str, ...]] = {
    "xgboost": ("xgboost",),
    "xgb": ("xgboost",),
    "lightgbm": ("lightgbm",),
    "lgbm": ("lightgbm",),
    "catboost": ("catboost",),
    "sklearn": ("sklearn",),
    "scikitlearn": ("sklearn",),
    "statsmodels": ("statsmodels",),
    "tensorflow": ("tensorflow", "keras"),
    "keras": ("keras", "tensorflow"),
    "pytorch": ("torch",),
    "torch": ("torch",),
}


def _claimed_libraries(model_type: str) -> dict[str, tuple[str, ...]]:
    """Library tokens the declared ``model_type`` string commits to.

    :param model_type: The declared free-text model type from the dossier.
    :type model_type: str
    :returns: The matching subset of :data:`_LIBRARIES`; empty when the
        declaration names no library at all (``isolation_forest_anomaly_
        detection``), in which case there is nothing to contradict.
    :rtype: dict[str, tuple[str, ...]]
    """
    squashed = "".join(char for char in model_type.lower() if char.isalnum())
    return {token: frags for token, frags in _LIBRARIES.items() if token in squashed}


def check_declared_model_type(stage_b: dict[str, Any], t01b: dict[str, Any],
                              model: Any, sink: FindingSink, source_phase: str) -> None:
    """Record a finding when the declared library contradicts the artefact.

    Silent unless the dossier names a library *and* none of the libraries it
    names appear in the loaded estimator's module path — so a declaration
    naming several (``xgboost_sklearn_wrapper``) needs only one to hold.

    :param stage_b: The raw Stage B Annex IV dossier.
    :param t01b: The stored T01b artefact; wins over ``stage_b`` as elsewhere.
    :param model: The estimator returned by the model loader.
    :param sink: Finding sink honouring the caller's emit flags.
    :param source_phase: Tag for the emitted finding.
    """
    declared = t01b.get("model_type") or stage_b.get("model_type")
    if not declared or model is None:
        return
    claimed = _claimed_libraries(str(declared))
    if not claimed:
        return
    actual = f"{type(model).__module__}.{type(model).__name__}"
    if any(frag in actual.lower() for frags in claimed.values() for frag in frags):
        return
    sink.add(make_finding(
        finding_id="P3-MODEL-TYPE-MISMATCH",
        description=(
            f"Declared model type '{declared}' names implementation library "
            f"'{max(claimed, key=len)}', but the submitted artefact loads as {actual}. "
            "The technical documentation does not describe the system actually "
            "assessed; every metric in this report was computed on the artefact, "
            "not on the declared model."
        ),
        materiality="possibly_material", articles=["Art.11", "Art.15"],
        source_phase=source_phase,
        recommendation="Correct the declared model type, or submit the artefact it describes.",
        declared=str(declared), observed=actual,
    ), load=True)
