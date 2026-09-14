"""Phase 2's examination of the dataset's labels for possible bias (Art. 10 §2(f))."""
from __future__ import annotations

from typing import Any

from aaa.tools.fairness_ci import FOUR_FIFTHS
from aaa.tools.findings import make_finding
from aaa.tools.label_disparity import label_disparity


def examine_label_bias(df: Any, data_available: bool, decl: dict[str, Any],
                       target: str | None, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the label examination and record a finding for each attribute it flags.

    Adverse impact the interval establishes is a possibly-material finding; a ratio
    the data cannot place against four-fifths is an observation that says so. The
    point ratio alone once raised the finding, and the Verifier read "a ratio of
    0.748 (four-fifths rule)" as a material breach its own interval did not support.

    :param df: The frame Phase 2 loaded.
    :param data_available: Whether that frame is the real dataset.
    :param decl: The Phase 2 dispatch (declared positive label and protected columns).
    :param target: The resolved target column.
    :param findings: Phase 2 findings, extended in place.
    :returns: The ``label_bias`` block for T07.
    """
    result = label_disparity(df if data_available else None, target, decl.get("positive_label", 1),
                             list(decl.get("sensitive_feature_columns") or []))
    for attr in (a for a in result["attributes"] if a.get("tested")):
        adverse = attr.get("four_fifths_passed") is False
        if attr.get("four_fifths_passed") is True:
            continue
        findings.append(make_finding(
            finding_id=f"P2-LABEL-BIAS-{attr['attribute'].upper()}",
            description=_description(attr, target, result["positive_label"], adverse),
            materiality="possibly_material" if adverse else "observation",
            articles=["Art.10", "Art.10§2(f)"], source_phase="P2",
            recommendation=(
                "Examine whether the disparity reflects bias in the decisions the data "
                "records, and document detection and mitigation measures (Art. 10 §2(f)-(g))."
                if adverse else
                "Examine the recorded decisions on a larger sample, or document why the "
                "disparity cannot be examined further (Art. 10 §2(f)).")))
    return result


def _description(attr: dict[str, Any], target: str | None, positive: Any, adverse: bool) -> str:
    """The measured rates, the interval, and what the interval decides."""
    interval = attr["ratio_interval"]
    measured = (f"The dataset's positive label ({target} = {positive}) across {attr['attribute']}: "
                f"{attr['lowest_group']} {_rate(attr, attr['lowest_group'])} against "
                f"{attr['highest_group']} {_rate(attr, attr['highest_group'])}, a ratio of "
                f"{attr['ratio']} ({int(interval['level'] * 100)}% interval "
                f"{interval['low']}–{interval['high']}, adjusted for "
                f"{interval['comparisons']} group comparison(s)). ")
    verdict = (f"The whole interval lies below the four-fifths ratio ({FOUR_FIFTHS}), so "
               "adverse impact in the recorded decisions is established." if adverse else
               f"The interval spans the four-fifths ratio ({FOUR_FIFTHS}): this sample "
               "establishes neither adverse impact nor its absence.")
    same = attr.get("same_grouping_as")
    repeat = (f" {attr['attribute']} divides these rows into exactly the same groups as {same}, "
              f"so these figures repeat {same}'s." if same else "")
    return (measured + verdict + repeat
            + " This examines the recorded decisions, not the model's outputs.")


def _rate(attr: dict[str, Any], group: str) -> str:
    """``rate (n=…)`` for *group*."""
    row = next(g for g in attr["groups"] if g["group"] == group)
    return f"{row['positive_rate']:.3f} (n={row['n']})"


def label_bias_fails(label_bias: dict | None) -> bool:
    """Whether any attribute's recorded labels are flagged: adverse, or undecided.

    Either one sits beside a finding in T07, and a PASS beside a finding
    contradicted itself (the Verifier held T07 for it, case 01, 2026-09-13).

    :param label_bias: :func:`aaa.tools.label_disparity.label_disparity` output.
    """
    return any(a.get("four_fifths_passed") is False
               or (a.get("tested") and a.get("four_fifths_passed") is None)
               for a in (label_bias or {}).get("attributes") or [])


__all__ = ["examine_label_bias", "label_bias_fails"]
