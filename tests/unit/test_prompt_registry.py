from __future__ import annotations

from aaa.platform import prompt_registry


REQUIRED_PROMPTS = [
    "orchestrator",
    "verifier",
    "regulatory_rag",
    "phase1_scope",
    "phase2_data",
    "phase3_model",
    "phase4_output",
    "phase5_governance",
    "phase6_report",
    "tier3_specialist",
    "hitl_escalation",
]


def test_load_prompt_returns_all_required_prompts():
    for name in REQUIRED_PROMPTS:
        prompt = prompt_registry.load_prompt(name)
        assert isinstance(prompt, str)
        assert len(prompt) > 200


def test_prompt_version_hash_changes_when_prompt_markdown_changes(monkeypatch):
    monkeypatch.setattr(prompt_registry, "_read_prompt_markdown", lambda: "alpha")
    first = prompt_registry.prompt_version_hash()
    monkeypatch.setattr(prompt_registry, "_read_prompt_markdown", lambda: "beta")
    second = prompt_registry.prompt_version_hash()
    assert first != second


def test_verifier_prompt_includes_materiality_requirements():
    prompt = prompt_registry.load_prompt("verifier")
    assert "materiality" in prompt.lower()
    assert "materiality_rationale" in prompt


def test_phase_prompts_include_client_doc_protocol_where_required():
    for name in ("phase1_scope", "phase2_data", "phase3_model", "phase5_governance"):
        prompt = prompt_registry.load_prompt(name)
        assert "client_doc_search" in prompt


def test_report_architect_prompt_includes_auditor_opinion_protocol():
    prompt = prompt_registry.load_prompt("phase6_report")
    assert "AUDITOR OPINION PROTOCOL" in prompt
