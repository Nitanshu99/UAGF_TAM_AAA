"""No tool may report a measurement it did not take.

The prompt-injection suite returned a hardcoded result on every call — 150
probes, 2 successful attacks, a 1.3 % vulnerability rate and a named finding,
*"Leaked system prompt via 'ignore instructions' variant."* — regardless of
whether there was an endpoint to probe. It never raised, so its own fallback was
unreachable. That invented security finding reached the narrative LLM, the T16
artefact, the client's report, and ``derive_verdict``, which gates FAIL on that
rate. Fabricated adversarial results in a conformity audit are the most
consequential form of the placeholder problem.

The rule these tests hold: measured, or explicitly not measured. Never a number
that looks measured.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from aaa.agents.tier3.uagf_tam_l.ragas_run import derive_verdict
from aaa.tools.prompt_injection_suite import prompt_injection_suite

SYSTEM_PROMPT = pathlib.Path("mock/06_mariposa_edu_gmbh/docs/system_prompt.txt")


def test_no_endpoint_means_no_probe_numbers() -> None:
    """The exact regression: no endpoint must not yield probe statistics."""
    result = prompt_injection_suite(target_uri=None, system_prompt=None)
    assert result["tested"] is False
    assert result["total_probes"] == 0
    assert result["vulnerability_rate"] is None
    assert result["critical_vulnerabilities"] == []
    assert "endpoint" in result["not_tested_reason"]


def test_the_invented_finding_is_gone() -> None:
    """It named a specific vulnerability that had never been observed."""
    for target in (None, "https://example.invalid/api"):
        result = prompt_injection_suite(target_uri=target, system_prompt="x" * 200)
        assert result["total_probes"] != 150
        assert result["vulnerability_rate"] != 0.013
        assert not any("Leaked system prompt" in v
                       for v in result["critical_vulnerabilities"])


def test_a_rate_of_none_is_never_a_clean_zero() -> None:
    """0.0 reads as "probed and clean"; the truth is "not probed"."""
    assert prompt_injection_suite(None, None)["vulnerability_rate"] is not 0.0  # noqa: F632


@pytest.mark.skipif(not SYSTEM_PROMPT.is_file(), reason="mock bundle not present")
def test_static_analysis_is_labelled_and_counts_nothing_it_did_not_do() -> None:
    """Reading a real prompt is legitimate — dressed as probing it is not."""
    result = prompt_injection_suite(None, SYSTEM_PROMPT.read_text("utf-8"))
    assert result["tested"] is False  # reading the prompt is not adversarial probing
    assert result["method"] == "static_prompt_analysis"
    assert "system prompt was read" in result["not_tested_reason"]
    assert result["total_probes"] == 0
    assert result["vulnerability_rate"] is None
    assert isinstance(result["observations"], list)


def test_an_unprobed_system_is_not_marked_failed_or_clean() -> None:
    """`derive_verdict` must treat a null rate as a missing measurement."""
    unprobed = prompt_injection_suite(None, None)
    verdict = derive_verdict({"pass_rate": 0.95}, {"faithfulness": 0.95}, unprobed)
    assert verdict == "PASS_WITH_OBSERVATIONS"


def _literal(node: ast.expr) -> bool:
    """Whether an expression is built entirely from literals."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(_literal(v) for v in node.values)
    return False


def test_no_tool_returns_a_dict_of_invented_numbers() -> None:
    """A sweep, so the next one is caught before it ships.

    A function returning a dict whose every value is a literal, including a
    number that is not 0 or 1, is reporting something it did not compute. Zero
    and one are exempt: an honest empty result is full of them.
    """
    offenders: list[str] = []
    for path in sorted(pathlib.Path("aaa").rglob("*.py")):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
                continue
            values = node.value.values
            if len(values) < 3 or not all(_literal(v) for v in values):
                continue
            if any(isinstance(v, ast.Constant) and isinstance(v.value, (int, float))
                   and not isinstance(v.value, bool) and v.value not in (0, 1)
                   for v in values):
                offenders.append(f"{path}:{node.lineno}")
    assert not offenders, f"invented measurements returned at: {offenders}"
