"""Running the RAGAs evaluation over the golden set, and the verdict its scores support."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.uagf_tam_l.ragas_verdict import derive_verdict
from aaa.agents.tier3.uagf_tam_l.scoring import score_rows


def run_golden_set(questions: list[str], answers: list[str],
                   expected: list[str]) -> dict[str, Any]:
    """Score answers against the golden reference set (fuzzy containment).

    A golden set exported before the system has been run against it carries
    reference answers and no system answers. Scoring that would mark every row
    failed and report a 0 % pass rate, which reads as "the system answered all
    55 wrongly" when the fact is "nobody has answered them yet". Those are
    different findings and only one of them is true, so this reports the set as
    **unscored** — ``pass_rate`` is ``None``, the way ``ragas_eval`` already
    reports a metric it could not compute.

    :param questions: Evaluation questions.
    :param answers: System answers under test; may be empty strings.
    :param expected: Reference answers.
    :returns: Pass/fail statistics with per-failure details, or an unscored
        result carrying ``pass_rate: None`` and the reason.
    """
    total = len(questions)
    if not total:
        return {
            "total_samples": 0,
            "passed_samples": 0,
            "failed_samples": 0,
            "pass_rate": None,
            "scored": False,
            "unscored_reason": (
                "No golden evaluation set was supplied, so answer quality could "
                "not be measured. Nothing here is derived from example data."),
            "failure_details": [],
        }
    if not any(a.strip() for a in answers):
        return {
            "total_samples": total,
            "passed_samples": 0,
            "failed_samples": 0,
            "pass_rate": None,
            "scored": False,
            "unscored_reason": (
                f"{total} reference question(s) supplied with no system answers "
                "to score against. The golden set was read; the system under "
                "test has not been run against it."),
            "failure_details": [],
        }
    passed, rows = score_rows(questions, answers, expected)
    return {
        "total_samples": total,
        "passed_samples": passed,
        "failed_samples": total - passed,
        "pass_rate": passed / total if total > 0 else 0.0,
        "scored": True,
        "failure_details": rows,
    }


__all__ = ["derive_verdict", "run_golden_set"]
