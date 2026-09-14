"""label_disparity — is the positive label distributed evenly across protected groups?

An examination of the *data* in view of possible biases (Art. 10 §2(f)): the rate
at which rows carry the positive label, per group of each declared protected
attribute. Where the label is a human decision, a
disparity here is a property of the decisions the evaluation set records — it is
not model-output fairness (T12) and does not need model access. No artefact
reported it, although the evaluation set held the target and five declared
protected attributes (T-20260913-034).
"""
from __future__ import annotations

from typing import Any

from aaa.tools.label_disparity.attribute import FOUR_FIFTHS, attribute_disparity, group_labels
from aaa.tools.label_disparity.partition import same_groupings

METHOD = ("positive-label rate per group; the ratio of each lower to each higher rate, with "
          "a Katz interval Bonferroni-adjusted over every pair of groups, decided against "
          "the four-fifths rule only where the interval lies wholly on one side of 0.8")


def label_disparity(df: Any, target: str | None, positive_label: Any,
                    attributes: list[str]) -> dict[str, Any]:
    """Examine the label's distribution across each declared protected attribute.

    :param df: The frame Phase 2 loaded.
    :param target: The declared target column.
    :param positive_label: The declared positive label.
    :param attributes: Declared protected-attribute columns.
    :returns: ``{computed, reason, method, target_column, positive_label, attributes}``.
    """
    base = {"method": METHOD, "target_column": target,
            "positive_label": None if positive_label is None else str(positive_label)}
    columns = set(getattr(df, "columns", []))
    missing = _missing_inputs(df, target, columns, attributes)
    if missing:
        return {**base, "computed": False, "attributes": [],
                "reason": f"not examined: {'; '.join(missing)}"}
    absent = [a for a in attributes if a not in columns]
    results, grouped = [], {}
    for attribute in (a for a in attributes if a in columns):
        rows = df[[attribute, target]].dropna()
        positive = [str(v) == str(positive_label) for v in rows[target].tolist()]
        labels = group_labels(attribute, rows[attribute].tolist())
        grouped[attribute] = (list(rows.index), labels)
        results.append(attribute_disparity(attribute, labels, positive))
    repeats = same_groupings(grouped)
    for result in results:
        result["same_grouping_as"] = repeats.get(result["attribute"])
    return {**base, "computed": True, "attributes": results,
            "reason": f"declared attributes absent from the dataset: {absent}" if absent else None}


def _missing_inputs(df: Any, target: str | None, columns: set[str],
                    attributes: list[str]) -> list[str]:
    """Each input the examination lacks, named exactly.

    One catch-all sentence ("no dataset, declared target column, or declared
    protected attribute") was returned for all of them; case 03 had its dataset
    and target and lacked only protected attributes, and the Verifier rejected T07
    as stating a falsehood.
    """
    if df is None:
        return ["no dataset was loaded"]
    missing = []
    if not target:
        missing.append("no target column declared")
    elif target not in columns:
        missing.append(f"declared target column {target!r} is not in the dataset")
    if not attributes:
        missing.append("no protected attribute declared, so there are no groups to compare")
    return missing


__all__ = ["FOUR_FIFTHS", "METHOD", "attribute_disparity", "label_disparity"]
