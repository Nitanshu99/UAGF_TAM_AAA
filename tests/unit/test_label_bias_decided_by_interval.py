"""Phase 2's label examination and the tools carry no fixed fairness number (T-20260914-024…026)."""
from __future__ import annotations

import jsonschema
import pandas as pd
import pytest

from aaa.agents.tier2.data_auditor.bias import examine_label_bias, label_bias_fails
from aaa.tools.template_render.logger import _load_schema

_DISPATCH = {"positive_label": 1, "sensitive_feature_columns": ["sex"]}


@pytest.fixture(name="case_05_frame")
def _case_05_frame() -> pd.DataFrame:
    """Case 05's recorded shortlist decisions by sex: 32 of 71 against 53 of 88."""
    rows = ([("male", int(i < 32)) for i in range(71)]
            + [("female", int(i < 53)) for i in range(88)])
    return pd.DataFrame({"sex": [r[0] for r in rows], "shortlist": [r[1] for r in rows]})


def test_an_undecided_label_ratio_is_an_observation_that_says_so(case_05_frame) -> None:
    """Not "a ratio of 0.748 (four-fifths rule)", which the Verifier read as a breach."""
    findings: list = []
    label_bias = examine_label_bias(case_05_frame, True, _DISPATCH, "shortlist", findings)
    assert [f["materiality"] for f in findings] == ["observation"]
    assert "establishes neither adverse impact nor its absence" in findings[0]["description"]
    assert label_bias_fails(label_bias)


def test_the_label_block_validates_against_t07(case_05_frame) -> None:
    """ratio_interval is in the schema, excluded_groups is gone from it."""
    label_bias = examine_label_bias(case_05_frame, True, _DISPATCH, "shortlist", [])
    jsonschema.validate(label_bias, _load_schema("T07_data_quality_report")["properties"]["label_bias"])


def test_no_verdict_band_or_minimum_is_left_in_the_fairness_tools() -> None:
    """The unsourced bands and the 30-row floor cannot come back through a re-export."""
    import aaa.tools.demographic_parity as dp
    import aaa.tools.disparate_impact as di
    import aaa.tools.equal_opportunity as eo
    import aaa.tools.fairness_groups as fg
    import aaa.tools.subgroup_metrics as sg

    names = {"_band", "_RATIO_PASS_THRESHOLD", "_DIFFERENCE_PASS_THRESHOLD",
             "_DIFFERENCE_OBSERVATION_THRESHOLD", "_ACCURACY_GAP_PASS_THRESHOLD",
             "_ACCURACY_GAP_OBSERVATION_THRESHOLD", "_FOUR_FIFTHS_THRESHOLD",
             "_OBSERVATION_THRESHOLD", "MIN_GROUP_SIZE"}
    for module in (dp, di, eo, fg, sg):
        assert not names & set(vars(module)), module.__name__


def test_an_attribute_that_repeats_another_grouping_says_so() -> None:
    """A second attribute that groups the rows exactly as nationality does says so."""
    from aaa.tools.label_disparity import label_disparity

    nations = ["AA"] * 60 + ["BB"] * 30 + ["CC"] * 20 + ["DD"] * 10
    frame = pd.DataFrame({
        "nationality": nations, "birth_country": nations,
        "first_language": ["xx" if n in ("CC", "DD") else n.lower() for n in nations],
        "advanced": [int(i % 3 == 0) for i in range(len(nations))]})
    attrs = label_disparity(frame, "advanced", 1,
                            ["nationality", "birth_country", "first_language"])["attributes"]
    repeats = {a["attribute"]: a["same_grouping_as"] for a in attrs}
    assert repeats == {"nationality": None, "birth_country": "nationality",
                       "first_language": None}


def test_every_tested_ratio_says_what_its_interval_decides(case_05_frame) -> None:
    """Case 01: a null four_fifths_passed with a null reason read as unexplained."""
    label_bias = examine_label_bias(case_05_frame, True, _DISPATCH, "shortlist", [])
    [attribute] = label_bias["attributes"]
    assert attribute["four_fifths_passed"] is None
    assert attribute["reason"].startswith("undecided: the ratio's interval")
