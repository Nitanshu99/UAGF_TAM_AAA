"""A measurement narrative is built from its artefact's own fields (T-20260913-067).

Phases 2–4 replaced the T07, T11 and T12 narratives with the LLM's reply, which
summarises the whole phase: case 03's T11 quoted metric-suite accuracy, macro-F1
and SHAP values beside its probe fields, and the Verifier refused it. The reply
remains the Report summary; the narratives keep only the provenance note.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_ASSIGNMENTS = {
    "aaa/agents/tier2/data_auditor/artefacts.py": "quality_narrative",
    "aaa/agents/tier2/model_validator/artefacts.py": "robustness_narrative",
    "aaa/agents/tier2/output_fairness/artefacts.py": "fairness_narrative",
}


@pytest.mark.parametrize("path,field", sorted(_ASSIGNMENTS.items()))
def test_the_llm_summary_never_becomes_a_measurement_narrative(path: str, field: str) -> None:
    tree = ast.parse(pathlib.Path(path).read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Subscript) and ast.unparse(target.slice).strip("'\"") == field:
            source = ast.unparse(node.value)
            assert "summary" not in source, f"{path}: {field} = {source}"
            return
    pytest.fail(f"{path} no longer assigns {field}; update this guard")
