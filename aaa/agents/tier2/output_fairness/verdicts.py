"""Translation of the suite verdict into findings and evidence gaps (step 7)."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.articles import EVIDENCED_ARTICLES, FINDING_ARTICLES
from aaa.agents.tier2.output_fairness.context import FairnessInputs, SuiteResult
from aaa.agents.tier2.output_fairness.findings import fairness_findings, insufficient_findings
from aaa.agents.tier2.output_fairness.skip_text import recommendation, skipped_reason
from aaa.tools.findings import make_finding


def refused_attributes(per_attribute: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attributes with fewer than two cohorts, so nothing to compare."""
    return [a for a in per_attribute if a.get("resolution", {}).get("tested") is False]


def undecided_attributes(per_attribute: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attributes measured, whose interval could not place the ratio against four-fifths."""
    return [a for a in per_attribute if a.get("verdict") == "INSUFFICIENT_EVIDENCE"]


def apply_verdict_findings(inp: FairnessInputs, suite: SuiteResult) -> str | None:
    """Translate the aggregate verdict into findings / insufficiency flags.

    The group-fairness metrics compare rates of a discrete outcome, so a regression
    model's continuous output is marked ``NOT_APPLICABLE``. An anomaly detector is not:
    its anomalous/normal flag is a binary outcome whose rate can differ by group, and
    case 03's high-risk Isolation Forest was declared out of fairness testing on model
    type alone (MiniMax run, 2026-09-14). It takes the untested path with its cause.

    :param inp: Phase 4 inputs; ``findings`` / ``insufficient`` are extended
        in place.
    :param suite: Suite result; ``overall_verdict`` may be rewritten to
        ``NOT_APPLICABLE``.
    :returns: The ``skipped_reason`` for T12, or ``None`` when tested.
    """
    refused = refused_attributes(suite.per_attribute)
    not_applicable = (suite.overall_verdict == "NOT_TESTED" and not refused
                      and inp.task_type == "regression")
    if not_applicable:
        suite.overall_verdict = "NOT_APPLICABLE"
        inp.findings.append(make_finding(
            finding_id="P4-FAIR-NA",
            # Fix 44 (R12): this read "not applicable to a anomaly model" in the
            # delivered PDF — a hard-coded "a" in front of an interpolated word.
            # "this" is correct before every value `_infer_task_type` returns and
            # every one it might later return, where an article chosen by vowel
            # sound would be a heuristic with a failure mode. It is also more
            # precise: the sentence is about the model under audit, not a class.
            description=(
                f"Group-fairness metrics are not applicable to this {inp.task_type} "
                "model: there is no per-group classification outcome to test. "
                "Non-discrimination is covered by Phase 3 accuracy/robustness and "
                "post-market monitoring."),
            materiality="observation", articles=FINDING_ARTICLES, source_phase="P4",
            recommendation=("Confirm the model is non-classification; "
                            "no group-fairness test required.")))
        return f"Group-fairness not applicable to this {inp.task_type} model."
    if suite.overall_verdict == "NOT_TESTED" and not refused:
        # The cause is established in `resolve_inputs`, not assumed here (F4).
        reason = skipped_reason(inp.skip_cause, inp.skip_detail)
        inp.insufficient.update(EVIDENCED_ARTICLES)
        inp.findings.append(make_finding(
            finding_id="P4-NOT-TESTED",
            description=f"Output fairness could not be tested. {reason}",
            materiality="possibly_material", articles=FINDING_ARTICLES, source_phase="P4",
            recommendation=recommendation(inp.skip_cause)))
        return reason
    inp.findings.extend(insufficient_findings(refused))
    inp.findings.extend(fairness_findings(suite.per_attribute))
    if refused or undecided_attributes(suite.per_attribute):
        # An article is unevidenced whenever *any* declared attribute went
        # untested or undecided: the audit was contracted to assess
        # non-discrimination, and it assessed part of it. Fix 26's gate makes the
        # same call one layer up.
        inp.insufficient.update(EVIDENCED_ARTICLES)
    if len(refused) == len(suite.per_attribute):
        return ("No protected attribute had two or more cohorts to compare; "
                "see group_resolution.")
    return None
