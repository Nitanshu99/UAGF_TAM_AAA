"""T12 output fairness report builder."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.context import FairnessInputs, SuiteResult


def build_t12(engagement_id: str, modality: str, inp: FairnessInputs,
              suite: SuiteResult, skipped_reason: str | None, now: str) -> dict[str, Any]:
    """Build the T12 output fairness report.

    :param engagement_id: Engagement identifier.
    :param modality: Normalised system modality.
    :param inp: Resolved Phase 4 inputs.
    :param suite: Fairness suite result.
    :param skipped_reason: Why the suite was skipped, if it was.
    :param now: ISO-8601 generation timestamp.
    :returns: T12 fairness-report dictionary.
    """
    return {
        "engagement_id": engagement_id,
        "modality": modality,
        "sensitive_features": list(inp.sensitive_feature_names),
        # Fix 27: the cohorts each metric was computed over — binned or not, how
        # many, how small, and whether the attribute was testable at all. Without
        # it a reader cannot tell a measured disparity from a binning artefact.
        "group_resolution": [a["resolution"] for a in suite.per_attribute
                             if a.get("resolution")],
        "evaluation_sample_size": suite.sample_size,
        "demographic_parity": suite.dp,
        "equal_opportunity": suite.eo,
        "disparate_impact": suite.di,
        "subgroup_metrics": suite.sg,
        "overall_fairness_verdict": suite.overall_verdict,
        "fairness_narrative": build_fairness_narrative(modality, suite),
        "skipped_reason": skipped_reason,
        # Fix 47 (R15). Two defects in three lines, and the second was found
        # auditing the first. (a) The note below used to be written whatever
        # happened, so a suite that never ran still reported "Bias detection
        # performed" — a claim about an examination that did not take place.
        # (b) The field beside it was `art15_1_compliance_notes`, reading
        # "Non-discrimination assessed per Art. 15 §1". Art. 15 §1 is accuracy,
        # robustness and cybersecurity; the bias-examination obligation is
        # Art. 10 §2(f), with Art. 9 risk management alongside it.
        "art10_2f_compliance_notes": _art10_2f_note(suite, skipped_reason),
        # Attribution, not a compliance claim: Phase 4 does not assess Art. 9,
        # and this note says where its result goes rather than what it proves.
        "art9_compliance_notes": (
            f"Aggregate output-fairness verdict: {suite.overall_verdict}. This is "
            "an input to the Art. 9 risk-management system; conformity with Art. 9 "
            "is assessed in Phase 5 and is not asserted here."),
        "generated_at": now,
    }


def _art10_2f_note(suite: SuiteResult, skipped_reason: str | None) -> str:
    """Say what the bias examination did, including when it did not run.

    :param suite: Fairness suite result.
    :param skipped_reason: Why the suite was skipped, if it was.
    :returns: A sentence that describes the examination actually performed.
    """
    if skipped_reason or suite.overall_verdict in {"NOT_TESTED", "NOT_APPLICABLE"}:
        return ("Bias examination under Art. 10 §2(f) was not performed: "
                f"{skipped_reason or suite.overall_verdict}.")
    return ("Bias examination performed per Art. 10 §2(f): four metric families "
            "(demographic parity, equal opportunity, disparate impact, subgroup "
            f"performance). Aggregate verdict: {suite.overall_verdict}.")


def build_fairness_narrative(modality: str, suite: SuiteResult) -> str:
    """Compose a short human-readable narrative for T12.

    :param modality: Normalised system modality.
    :param suite: Fairness suite result.
    :returns: Narrative paragraph for T12.
    """
    untestable = [a["resolution"]["reason"] for a in suite.per_attribute
                  if a.get("resolution", {}).get("tested") is False]
    if suite.overall_verdict == "NOT_TESTED" and not untestable:
        return (f"Fairness suite could not be executed for {modality} modality — "
                "no predictions or sensitive features supplied.")
    grouping = " ".join(untestable)
    if suite.overall_verdict == "NOT_TESTED":
        return f"No attribute was testable on this evaluation set. {grouping}".strip()
    return (
        f"{modality} fairness verdict: {suite.overall_verdict}. "
        f"Demographic parity: {suite.dp['verdict']} (diff={suite.dp.get('difference')}). "
        f"Equal opportunity: {suite.eo['verdict']} (diff={suite.eo.get('difference')}). "
        f"Disparate impact: {suite.di['verdict']} (ratio={suite.di.get('ratio')}). "
        f"Subgroup performance: {suite.sg['verdict']} "
        f"(accuracy_gap={suite.sg.get('accuracy_gap')}). {grouping}").strip()
