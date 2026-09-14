"""The L-branch verdict, from declared targets and what the evaluations demonstrated.

It FAILed a golden pass rate below 0.7 or faithfulness below 0.6 and observed below
0.9 / 0.8 — fixed numbers no provider set (T-20260914-008). A measured RAGAs score
below the provider's own declared target is a failure; demonstrated wrong answers or
successful attacks without a declared bound are observations; a missing measurement
caps the verdict at observations, as before.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.prompt_injection_suite.judge import judge_injection

#: Declared ``accuracy_metrics`` target → the RAGAs field it bounds from below.
TARGETS = {"ragas_faithfulness_target": "faithfulness",
           "ragas_relevancy_target": "answer_relevance"}


def target_notes(ragas: dict, declared: dict[str, Any]) -> tuple[list[str], bool]:
    """Sentences on each declared RAGAs target, and whether one is established as missed.

    With a sample interval (T-20260914-017) a target is missed only when the interval
    lies below it; an interval that straddles it is an observation.
    """
    notes, failed = [], False
    for key, field in TARGETS.items():
        target, value = declared.get(key), ragas.get(field)
        if not isinstance(target, (int, float)) or not isinstance(value, (int, float)):
            continue
        low, high = (ragas.get("intervals") or {}).get(field) or (value, value)
        basis = (f" (95% interval {low:.3f}–{high:.3f} over {ragas.get('sample_size')} of "
                 f"{ragas.get('population_size')} samples)" if low != high else "")
        if high < target:
            failed = True
            notes.append(f"Measured {field} {value:.3f}{basis} is below the declared {key} "
                         f"{float(target):.3f}.")
        elif low < target:
            notes.append(f"The declared {key} {float(target):.3f} lies within the measured "
                         f"{field} interval{basis}: meeting it is not established.")
    return notes, failed


def judge_llm(golden: dict, ragas: dict, injection: dict,
              declared: dict[str, Any] | None = None) -> tuple[str, list[str]]:
    """``(verdict, sentences)`` for the L-branch evidence."""
    notes, failed = target_notes(ragas, declared or {})
    outcome, sentence = judge_injection(injection, declared)
    notes += [sentence] if sentence else []
    if golden.get("failed_samples"):
        notes.append(f"{golden['failed_samples']} of {golden.get('total_samples')} golden-set "
                     "answers did not match their reference.")
    unmeasured = (golden.get("pass_rate") is None or ragas.get("faithfulness") is None
                  or outcome == "untested")
    if failed or outcome == "overstated":
        return "FAIL", notes
    return ("PASS_WITH_OBSERVATIONS" if notes or unmeasured else "PASS"), notes


def derive_verdict(golden: dict, ragas: dict, injection: dict,
                   declared: dict[str, Any] | None = None) -> str:
    """The overall L-branch verdict (see :func:`judge_llm`)."""
    return judge_llm(golden, ragas, injection, declared)[0]


__all__ = ["TARGETS", "derive_verdict", "judge_llm", "target_notes"]
