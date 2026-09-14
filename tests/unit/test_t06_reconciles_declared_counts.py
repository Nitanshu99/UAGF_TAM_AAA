"""T06 reconciles the declared dataset size with the file supplied (T-20260914-038, case 01)."""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t06.instances import feature_count, instances_type
from aaa.agents.tier2.data_auditor.t06.measured import DatasetMeasurement

_DECLARED = ("FinClear proprietary credit dataset -- 1000 instances, 20 attributes "
             "(7 numerical, 13 categorical), binary target.")


def _measured(rows: int = 700, attributes: int = 20) -> DatasetMeasurement:
    """A training file with *attributes* columns plus ``credit_risk``."""
    columns = tuple(f"a{i}" for i in range(attributes)) + ("credit_risk",)
    return DatasetMeasurement("minio://e/training.csv", rows, len(columns), columns, 0.0, ())


def test_the_target_is_not_an_attribute() -> None:
    """21 columns with the declared target are 20 attributes."""
    assert feature_count(_measured(), "credit_risk") == 20
    assert feature_count(_measured(), None) == 21


def test_a_declared_count_the_file_lacks_is_named() -> None:
    """1,000 declared, 700 supplied — stated, not left beside a contradicting number."""
    text = instances_type(_DECLARED, _measured(), "training", "credit_risk")
    assert text.startswith(_DECLARED)
    assert "700 rows x 21 columns (20 attributes plus the target)" in text
    assert "1000 instances declared, 700 supplied" in text
    assert "attributes declared" not in text


def test_matching_counts_raise_no_difference() -> None:
    """A file that has what was declared carries no reconciliation sentence."""
    text = instances_type(_DECLARED, _measured(1000), "training", "credit_risk")
    assert "differ" not in text


def test_t07_names_the_same_difference() -> None:
    """Case 01 w1a1: T07 printed 700 rows beside the declared 1000 instances."""
    from aaa.agents.tier2.data_auditor.declared_counts import declared_size

    t01b = {"training_data_description": _DECLARED, "training_dataset_uri": "minio://e/training.csv"}
    decl = {"stage_b": {"data_dictionary": {"target_column": "credit_risk"}}}
    sentence = declared_size(t01b, decl, {"measurement": _measured()})
    assert "1000 instances declared, 700 supplied" in sentence
    assert declared_size({**t01b, "training_dataset_uri": None}, decl,
                         {"measurement": _measured()}) == ""


def test_every_t06_field_states_counts_and_intervals_the_same_way() -> None:
    """Case 06 x1a1: "13 attributes plus the target" beside "14 columns" read as a mismatch."""
    from aaa.agents.tier2.data_auditor.t06.subpopulations import impact_on_subpopulations

    assert "rows x 21 columns (20 attributes plus the target)" in instances_type(
        _DECLARED, _measured(), "evaluation", "credit_risk")
    label_bias = {"computed": True, "target_column": "advanced", "attributes": [{
        "attribute": "region", "tested": True, "ratio": 0.62, "lowest_group": "B",
        "highest_group": "A", "four_fifths_passed": None,
        "ratio_interval": {"low": 0.41, "high": 0.93}}]}
    assert "interval 0.41–0.93, which spans 0.8" in (impact_on_subpopulations(label_bias) or "")


def test_each_attribute_names_its_four_fifths_decision() -> None:
    """T-20260914-064: case 06's CLI Verifier refused T06 for leaving the decision implied."""
    from aaa.agents.tier2.data_auditor.t06.subpopulations import impact_on_subpopulations

    def attr(name: str, passed: bool | None, low: float, high: float) -> dict:
        return {"attribute": name, "tested": True, "ratio": round((low + high) / 2, 4),
                "lowest_group": "a", "highest_group": "b", "four_fifths_passed": passed,
                "ratio_interval": {"low": low, "high": high}}
    text = impact_on_subpopulations({"computed": True, "target_column": "y", "attributes": [
        attr("sex", True, 0.85, 1.1), attr("age_band", None, 0.69, 1.21),
        attr("nationality", False, 0.4, 0.7)]}) or ""
    assert "nationality 0.55 (a vs b; interval 0.4–0.7, wholly below 0.8; four-fifths decision: adverse)" in text
    assert "age_band 0.95 (a vs b; interval 0.69–1.21, which spans 0.8; four-fifths decision: undecided)" in text
    assert "sex 0.975 (a vs b; interval 0.85–1.1, at or above 0.8; four-fifths decision: within)" in text
