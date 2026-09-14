"""The dataset's labels are examined across protected groups (Art. 10 §2(f)).

No artefact reported the human-decision label disparity an evaluation set
records (T-20260913-034).
"""
from __future__ import annotations

import pandas as pd

from aaa.agents.tier2.data_auditor.bias import examine_label_bias
from aaa.tools.label_disparity import label_disparity


def _frame() -> pd.DataFrame:
    """Group A advances 60 of 100, group B 30 of 100, group C all 10 of 10."""
    rows = ([("A", 1)] * 60 + [("A", 0)] * 40 + [("B", 1)] * 30 + [("B", 0)] * 70
            + [("C", 1)] * 10)
    return pd.DataFrame({"origin": [r[0] for r in rows], "advanced": [r[1] for r in rows]})


def test_every_group_is_kept_and_the_interval_decides() -> None:
    """No 10-row exclusion: C is compared too, and B against C is established adverse."""
    attr = label_disparity(_frame(), "advanced", 1, ["origin"])["attributes"][0]
    assert attr["four_fifths_passed"] is False
    assert {g["group"] for g in attr["groups"]} == {"A", "B", "C"}
    assert (attr["lowest_group"], attr["highest_group"], attr["ratio"]) == ("B", "C", 0.3)
    assert attr["ratio_interval"]["high"] < 0.8
    assert attr["ratio_interval"]["comparisons"] == 3
    assert "excluded_groups" not in attr


def test_one_group_is_untested_with_a_reason() -> None:
    """A single group cannot yield a ratio."""
    frame = pd.DataFrame({"origin": ["A"] * 45, "advanced": [1] * 40 + [0] * 5})
    attr = label_disparity(frame, "advanced", 1, ["origin"])["attributes"][0]
    assert attr["tested"] is False and "fewer than two groups" in attr["reason"]


def test_nothing_to_examine_says_so() -> None:
    """No dataset: not computed, rather than computed over nothing."""
    result = label_disparity(None, "advanced", 1, ["origin"])
    assert result["computed"] is False and result["attributes"] == []


def test_an_adverse_attribute_becomes_a_phase2_finding() -> None:
    """Cited to Art. 10 and §2(f), and explicit that it concerns recorded decisions."""
    findings: list = []
    examine_label_bias(_frame(), True, {"positive_label": 1, "sensitive_feature_columns": ["origin"]},
                       "advanced", findings)
    assert findings[0]["finding_id"] == "P2-LABEL-BIAS-ORIGIN"
    assert "Art.10§2(f)" in findings[0]["eu_ai_act_articles"]
    assert "not the model's outputs" in findings[0]["description"]
