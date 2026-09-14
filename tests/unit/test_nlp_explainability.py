"""Token-importance explainability for NLP pipelines (T10 global evidence)."""
from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.explainability import run_explainability
from aaa.tools.text_explain import token_importance

_TEXTS = ["python developer with sql skills", "warehouse operative forklift",
          "sql analyst reporting dashboards", "forklift driver logistics depot",
          "python data engineer pipelines", "logistics warehouse picker"] * 5
_LABELS = [1, 0, 1, 0, 1, 0] * 5


def _fitted_pipeline() -> Pipeline:
    """Small fitted TF-IDF + logistic regression text classifier."""
    pipe = Pipeline([("tfidf", TfidfVectorizer()),
                     ("clf", LogisticRegression(max_iter=200))])
    return pipe.fit(_TEXTS, _LABELS)


def test_token_importance_returns_ranked_tokens():
    """A fitted tfidf+logreg pipeline yields non-empty ranked token weights."""
    result = token_importance(model=_fitted_pipeline(), top_k=5)
    assert result["technique"] == "token_importance"
    assert result["tool"] == "text_explain"
    fi = result["feature_importance"]
    assert 0 < len(fi) <= 5
    assert [e["rank"] for e in fi] == list(range(1, len(fi) + 1))
    assert all(isinstance(e["feature"], str) and e["importance"] >= 0 for e in fi)


def test_token_importance_strips_columntransformer_prefix():
    """ColumnTransformer feature prefixes (tfidf__token) are stripped."""
    import pandas as pd
    frame = pd.DataFrame({"cv_text": _TEXTS})
    pipe = Pipeline([
        ("features", ColumnTransformer([("tfidf", TfidfVectorizer(), "cv_text")])),
        ("clf", LogisticRegression(max_iter=200)),
    ]).fit(frame, _LABELS)
    fi = token_importance(model=pipe)["feature_importance"]
    assert fi and not any("__" in e["feature"] for e in fi)


def test_token_importance_fails_soft_on_unsupported_model():
    """Non-pipeline input degrades to the empty T10 sub-schema, not a raise."""
    result = token_importance(model=object())
    assert result == {"technique": "none", "feature_importance": [],
                      "sample_size": None, "tool": None}


def test_run_explainability_routes_nlp_to_token_importance():
    """nlp modality with a linear text pipeline reports token_importance."""
    ctx = EvalContext(t01a={}, t01b={}, stage_b={}, model=_fitted_pipeline())
    expl = run_explainability({}, "nlp", ctx)
    assert expl.techniques == ["token_importance"]
    assert expl.global_expl["feature_importance"]


def test_run_explainability_nlp_falls_back_without_pipeline():
    """nlp modality without a usable pipeline uses the generic SHAP path."""
    ctx = EvalContext(t01a={}, t01b={}, stage_b={}, model=None)
    expl = run_explainability({}, "nlp", ctx)
    assert "token_importance" not in expl.techniques
