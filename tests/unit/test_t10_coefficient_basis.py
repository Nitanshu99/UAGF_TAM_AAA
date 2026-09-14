"""T-20260913-106: coefficient importances report no sample size, and say what they are.

Case 05's T10 wrote the vectorizer's 742 terms into ``sample_size``; the Verifier
read 742 records explained against a 240-record corpus and escalated it.
"""
from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from aaa.agents.tier2.model_validator.context import EvalContext
from aaa.agents.tier2.model_validator.explainability import run_explainability
from aaa.agents.tier2.model_validator.t10 import build_t10
from aaa.platform.evidence.contract import artefact_schema_errors

_TEXTS = pd.DataFrame({"cv_text": ["sql and python", "forklift and pallets", "python testing",
                                   "pallets and loading"] * 3})


def test_the_global_block_has_no_sample_size_and_the_narrative_names_the_basis() -> None:
    """``sample_size`` is null; the interpretation names coefficients over N terms."""
    vec = ColumnTransformer([("tfidf", TfidfVectorizer(ngram_range=(1, 2)), "cv_text")])
    model = Pipeline([("features", vec), ("clf", LogisticRegression())])
    model.fit(_TEXTS, [1, 0, 1, 0] * 3)
    terms = len(vec.get_feature_names_out())
    expl = run_explainability({}, "nlp", EvalContext(t01a={}, t01b={}, stage_b={},
                                                     model=model, x_eval=_TEXTS))
    t10 = build_t10("eng", "nlp", expl, "2026-09-13T00:00:00Z")
    assert t10["global_explanation"]["sample_size"] is None
    assert "vocabulary_size" not in t10["global_explanation"]
    assert f"coefficients over its {terms} vectorizer terms" in t10["interpretation"]
    assert not artefact_schema_errors("T10_explainability_report", t10)
