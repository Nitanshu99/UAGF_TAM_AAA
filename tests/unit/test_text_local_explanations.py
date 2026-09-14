"""T-20260913-098: a vectorizer + linear text pipeline explains individual decisions.

Case 05's T10 had global token importances and ``local_explanations`` null, so the
Verifier escalated it and Art. 13 went unassessed. For a linear model the per-token
contributions of one instance, plus the intercept, are its decision score exactly.
"""
from __future__ import annotations

import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.explainability import run_explainability
from aaa.tools.text_explain import token_contributions

_TEXTS = pd.DataFrame({"cv_text": ["sql and python", "forklift and pallets", "python testing",
                                   "pallets and loading", "sql testing", "loading dock"] * 3})
_Y = [1, 0, 1, 0, 1, 0] * 3


def _pipeline(clf) -> Pipeline:
    features = ColumnTransformer([("tfidf", TfidfVectorizer(), "cv_text")])
    return Pipeline([("features", features), ("clf", clf)]).fit(_TEXTS, _Y)


def test_contributions_and_intercept_are_the_decision_score() -> None:
    """Exact, not approximated: every token of the row, summed, gives the score."""
    model = _pipeline(LogisticRegression())
    local = token_contributions(model, _TEXTS, num_instances=2, num_features=50)
    assert len(local) == 2 and local[0]["prediction"] == "1"
    total = sum(t["contribution"] for t in local[0]["top_features"])
    intercept = float(model.steps[-1][1].intercept_[0])
    assert total + intercept == pytest.approx(float(model.decision_function(_TEXTS[:1])[0]))
    assert local[0]["explained_output"] == "decision score (log-odds) for class 1"


def test_a_non_linear_head_explains_nothing_and_says_why() -> None:
    """No proxy for a model the decomposition does not describe."""
    reasons: list[str] = []
    assert token_contributions(_pipeline(RandomForestClassifier(n_estimators=3)), _TEXTS,
                               reasons=reasons) == []
    assert reasons and "token contributions not computed" in reasons[0]


def test_the_nlp_route_records_the_local_technique() -> None:
    """T10 names the technique it ran and carries the five instances LIME would take."""
    ctx = EvalContext(t01a={}, t01b={}, stage_b={}, model=_pipeline(LogisticRegression()),
                      x_eval=_TEXTS)
    expl = run_explainability({}, "nlp", ctx)
    assert expl.techniques == ["token_importance", "token_contribution"]
    assert len(expl.local_expl) == 5 and not expl.degraded
