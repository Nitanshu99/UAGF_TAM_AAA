"""Real-auditor behaviour: data-dictionary inference and overrides."""
from __future__ import annotations

from aaa.tools.data_dictionary import resolve_data_dictionary


def test_data_dictionary_inference():
    cols = ["checking_status", "credit_amount", "age", "personal_status",
            "foreign_worker", "credit_risk"]
    dd = resolve_data_dictionary({}, cols)
    assert dd.target_column == "credit_risk"
    assert set(dd.sensitive_feature_columns) == {"age", "personal_status",
                                                 "foreign_worker"}
    assert dd.assumptions  # undeclared → assumptions recorded
    assert dd.is_usable()


def test_data_dictionary_explicit_overrides():
    cols = ["f1", "f2", "label"]
    dd = resolve_data_dictionary(
        {"target_column": "label", "positive_label": 1,
         "sensitive_feature_columns": ["f1"]},
        cols,
    )
    assert dd.target_column == "label"
    assert dd.target_explicit is True
    assert dd.sensitive_feature_columns == ["f1"]
