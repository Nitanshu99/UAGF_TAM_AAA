"""Scoring the golden-set rows the harness answered, row by row."""
from __future__ import annotations

from typing import Any


def score_rows(questions: list, answers: list, expected: list) -> tuple[int, list]:
    """Score each answered row against its reference.

    :param questions: The golden set's questions.
    :param answers: The system's answers, aligned to *questions*.
    :param expected: The reference answers, aligned to *questions*.
    :returns: ``(passed, failure_details)``.
    """
    passed = 0
    details: list[dict[str, Any]] = []
    for q, a, e in zip(questions, answers, expected):
        is_pass = (e.lower() in a.lower()) or (a.lower() in e.lower())
        if is_pass:
            passed += 1
        else:
            details.append({
                "sample_id": f"q_{len(details)}",
                "input": q,
                "expected": e,
                "actual": a,
                "reason": "Answer does not sufficiently cover expected reference.",
            })
    return passed, details


__all__ = ["score_rows"]
