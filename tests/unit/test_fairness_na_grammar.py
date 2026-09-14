"""Fix 44 — the indefinite article in `P4-FAIR-NA` (finding R12).

The delivered PDF read *"Group-fairness metrics are not applicable to a anomaly
model"* — a hard-coded "a" in front of an interpolated word. Client-facing prose,
verbatim, in case 03 #027.
"""
from __future__ import annotations

import re

import pytest

from aaa.agents.tier2.output_fairness.context import FairnessInputs, SuiteResult
from aaa.agents.tier2.output_fairness.verdicts import apply_verdict_findings

#: Every value `aaa.tools.eval_inputs.scoring._infer_task_type` can return, plus
#: the dataclass default. The branch only fires for two of them; the sentence has
#: to read correctly for all, because a value it cannot produce today is exactly
#: the kind that arrives later.
TASK_TYPES = ("anomaly", "regression", "classification", "unknown")

#: Words a following "a"/"an" would have to agree with. `anomaly` is the one the
#: run actually rendered wrong.
VOWEL_INITIAL = {"anomaly", "unknown"}


def _finding(task_type: str) -> tuple[dict | None, str | None]:
    inp = FairnessInputs(stage_b={}, task_type=task_type)
    suite = SuiteResult(per_attribute=[], sample_size=0, dp={}, eo={}, di={}, sg={},
                        overall_verdict="NOT_TESTED")
    skipped = apply_verdict_findings(inp, suite)
    na = [f for f in inp.findings if f["finding_id"] == "P4-FAIR-NA"]
    return (na[0] if na else None), skipped


@pytest.mark.parametrize("task_type", TASK_TYPES)
def test_no_stranded_indefinite_article_before_the_task_type(task_type):
    finding, skipped = _finding(task_type)
    for text in (finding["description"] if finding else "", skipped or ""):
        assert f" a {task_type} " not in text, f"reads 'a {task_type}'"
        assert f" an {task_type} " not in text or task_type not in VOWEL_INITIAL


@pytest.mark.parametrize("task_type", ["regression"])
def test_the_sentence_names_the_model_under_audit(task_type):
    finding, skipped = _finding(task_type)
    assert f"this {task_type} model" in finding["description"]
    assert f"this {task_type} model" in skipped


def test_the_run_s_own_sentence_is_correct_now():
    """Case 03 #027's sentence shape, on the model type that still takes the branch."""
    finding, _ = _finding("regression")
    assert "not applicable to a regression model" not in finding["description"]
    assert ("Group-fairness metrics are not applicable to this regression model"
            in finding["description"])


@pytest.mark.parametrize("task_type", TASK_TYPES)
def test_the_sentence_is_well_formed_for_every_task_type(task_type):
    """No double spaces, no dangling article, terminated."""
    finding, _ = _finding(task_type)
    if finding is None:
        return                      # classification/unknown take a different branch
    text = finding["description"]
    assert "  " not in text
    assert not re.search(r"\b(a|an)\s+(a|an)\b", text)
    assert text.rstrip().endswith(".")


def test_the_verdict_logic_itself_is_untouched():
    """NOT_APPLICABLE is for a continuous output only (T-20260914-040 moved anomaly off it)."""
    finding, skipped = _finding("regression")
    assert finding["materiality"] == "observation"
    assert skipped
    for task_type in ("anomaly", "classification", "unknown"):
        finding, _ = _finding(task_type)
        assert finding is None, "an anomaly flag is a discrete outcome"


def test_no_other_article_before_an_interpolation_survives_in_aaa():
    """The sibling sweep the backlog asked for, kept as a guard."""
    import re as _re
    from pathlib import Path

    pattern = _re.compile(r'\b(?:a|an)\s+\{')
    offenders = [
        f"{path}:{n}"
        for path in Path("aaa").rglob("*.py")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if pattern.search(line) and not line.lstrip().startswith("#")
    ]
    assert not offenders, f"article before an interpolation: {offenders}"
