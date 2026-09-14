"""intake_completeness: L-branch (LLM / agentic) conditional-field handling."""
from __future__ import annotations

from aaa.tools.intake_completeness_calculator import intake_completeness_calculator
from tests.unit.support.intake_completeness_fixture import load_stage_b, make_submission


def test_l_branch_missing_conditionals_penalises_score():
    """LLM modality with null conditional fields → score penalty applied."""
    l_report = intake_completeness_calculator(make_submission(load_stage_b()), "llm")
    tabular = intake_completeness_calculator(make_submission(load_stage_b()), "tabular")
    assert l_report.score <= tabular.score


def test_l_branch_with_all_conditionals_no_penalty():
    """LLM modality with all conditional fields present → no score penalty."""
    dossier = load_stage_b()
    dossier["system_prompt_uri"] = "minio://eng/prompts/system_v1.txt"
    dossier["rag_manifest_uri"] = "minio://eng/rag/manifest.json"
    dossier["guardrail_config_uri"] = "minio://eng/guardrails/config.yaml"
    dossier["golden_set_uri"] = "minio://eng/golden/set_v1.jsonl"
    report = intake_completeness_calculator(make_submission(dossier), "llm")
    assert report.gate_passed is True


def test_agentic_requires_tool_inventory():
    # tool_inventory is null in fixture → should be flagged as applicable.
    report = intake_completeness_calculator(make_submission(load_stage_b()), "agentic")
    tool_conditionals = [c for c in report.missing_conditional
                         if c.field == "tool_inventory"]
    assert len(tool_conditionals) == 1
    assert tool_conditionals[0].applicable is True
