"""Every T15 question is read, and a declared management-system standard is recorded.

Split from test_artefacts_quote_provider_documents.py (T-20260913-100); the
grounded answers come from the provider's documents (T-20260913-032/035/041).
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15 import T15_QUESTIONS, build_t15
from tests.unit.support.provider_documents import CGSA, DOSSIER_B, NOW


def test_every_t15_question_key_is_read_by_the_builder() -> None:
    """A question nobody reads is a search the audit pays for and ignores."""
    import inspect

    from aaa.agents.tier2.governance_agent.t15 import articles, evidence, questions, tools

    source = "".join(inspect.getsource(m) for m in (evidence, articles, questions, tools))
    for question in T15_QUESTIONS:
        base = question.key.removesuffix("_operating").removesuffix("_absent")
        if base in ("accuracy", "fairness", "field_data", "incidents"):
            continue  # read through grading.states.SOURCES
        assert f'"{base}"' in source, question.key


def test_t15_records_a_declared_management_system_standard() -> None:
    """T15 records a declared management system standard."""
    dossier = {**DOSSIER_B, "other_standards": [
        "ISO/IEC 23894:2023 (guidance, uncertified)",
        "ISO/IEC 42001:2023 (guidance, uncertified)"]}
    qms = build_t15("eng", dossier, CGSA, NOW)["art17_qms"]
    assert qms["qms_standard_referenced"] == "ISO/IEC 42001:2023 (guidance, uncertified)"
    assert "not a harmonised standard" in qms["rationale"]
    assert build_t15("eng", DOSSIER_B, CGSA, NOW)["art17_qms"]["qms_standard_referenced"] is None
