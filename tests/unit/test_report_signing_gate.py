"""Fix 10 / finding F15 — a plan is not an artefact, and a signature is earned.

Case 01 call #035: the ReportArchitect returned
``{"artefact_uri": "", "summary": "", "confidence": 0.0, "report_signed": true,
"retrieval_plan": {...}}`` — a signed audit report that was a to-do list.  Two
defects in one reply: the terminal round was never declared terminal and a
plan-shaped answer was accepted as the phase's artefact, and the strongest claim
the system makes was the one field nothing gated.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from aaa.agents.tier2.report_architect.report import assemble_report
from aaa.agents.tier2.report_architect.signing import signing_status
from aaa.agents.tier2.report_architect.t18 import build_t18
from aaa.tools.evidence_retrieval import (
    TERMINAL_NOTICE,
    RetrievalPlanNotAnsweredError,
    acompletion_json_react,
    close_retrieval,
    terminal_block,
)

_PLAN = {"retrieval_plan": {"regulatory_queries": ["Article 10 data governance"],
                            "client_doc_queries": []}}


def _signed_t18(**over) -> dict:
    base = {"executive_summary": "Twelve of fourteen articles are unevidenced.",
            "report_status": "FINAL"}
    return {**base, **over}


# --------------------------------------------------------------------------
# The terminal round is declared terminal
# --------------------------------------------------------------------------
def test_the_last_round_carries_the_terminal_notice():
    block = terminal_block(1, ["q"], [], final=True)

    assert block["final_round"] is True
    assert block["notice"] == TERMINAL_NOTICE
    assert "retrieval_plan" in TERMINAL_NOTICE, "the rule must name the rejected field"


def test_a_non_final_round_carries_no_notice():
    block = terminal_block(1, ["q"], [], final=False)

    assert block["final_round"] is False
    assert "notice" not in block


def test_the_loop_declares_its_last_round_final():
    seen: list[dict] = []

    class _Agent:
        name = "Fake"

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            seen.append(payload)
            return dict(_PLAN)

    class _Rag:
        def search(self, query, top_k=3):  # noqa: ARG002
            return [{"source_uri": "euaiact://Article_10", "text": "…", "score": 0.4}]

    with pytest.raises(RetrievalPlanNotAnsweredError):
        asyncio.run(acompletion_json_react(
            _Agent(), "phase2_data", {}, rag=_Rag(), engagement_id="", rounds=1))

    expansion = seen[1]["retrieval_expansion"]
    assert expansion["final_round"] is True
    assert expansion["notice"] == TERMINAL_NOTICE


# --------------------------------------------------------------------------
# A plan in the terminal position is refused
# --------------------------------------------------------------------------
def test_a_plan_at_the_close_is_re_prompted_once_with_retrieval_closed():
    seen: list[dict] = []

    class _Agent:
        name = "DataAuditor"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            seen.append(payload)
            type(self).calls += 1
            return {"summary": "Art. 10 assessed.", "confidence": 0.7}

    result = asyncio.run(close_retrieval(_Agent(), "phase2_data", {"task": "t"}, dict(_PLAN)))

    assert _Agent.calls == 1, "exactly one closing re-prompt"
    assert seen[0]["retrieval_expansion"]["retrieval_closed"] is True
    assert result["summary"] == "Art. 10 assessed."
    assert "retrieval_plan" not in result


def test_planning_again_after_the_close_raises_rather_than_filing_the_plan():
    class _Agent:
        name = "DataAuditor"

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            return dict(_PLAN)

    with pytest.raises(RetrievalPlanNotAnsweredError, match="retrieval was closed"):
        asyncio.run(close_retrieval(_Agent(), "phase2_data", {}, dict(_PLAN)))


def test_an_answer_passes_through_untouched_without_a_re_prompt():
    class _Agent:
        name = "DataAuditor"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            type(self).calls += 1
            return {}

    answer = {"summary": "done", "confidence": 0.8}
    result = asyncio.run(close_retrieval(_Agent(), "phase2_data", {}, answer))

    assert result == answer
    assert _Agent.calls == 0


def test_call_009_the_replanning_reply_no_longer_becomes_the_phase_artefact():
    """#009 verbatim: pass B re-planned, and the plan was returned as the report."""
    class _Agent:
        name = "DataAuditor"
        calls = 0

        async def acompletion_json(self, prompt_name, payload):  # noqa: ARG002
            type(self).calls += 1
            if type(self).calls <= 2:
                return {"message_type": "Report", "phase_id": "P2",
                        "summary": "Retrieving Article 10 regulatory text …",
                        "confidence": 0.0, **_PLAN}
            return {"message_type": "Report", "phase_id": "P2",
                    "summary": "Art. 10 assessed; num_instances = 1000.",
                    "confidence": 0.7}

    class _Rag:
        def search(self, query, top_k=3):  # noqa: ARG002
            return [{"source_uri": "euaiact://Article_10", "text": "…", "score": 0.4}]

    result = asyncio.run(acompletion_json_react(
        _Agent(), "phase2_data", {}, rag=_Rag(), engagement_id="", rounds=1))

    assert "retrieval_plan" not in result
    assert result["confidence"] == 0.7


# --------------------------------------------------------------------------
# The signing gate
# --------------------------------------------------------------------------
def test_a_complete_report_is_signed():
    signed, withheld = signing_status(_signed_t18(), "minio://t18.json",
                                      "An auditor's summary.", True)

    assert (signed, withheld) == (True, [])


def test_call_035_an_empty_report_is_not_signed():
    """The assessed reply: no URI, no summary, no synthesis — yet signed."""
    signed, withheld = signing_status(
        {"executive_summary": "", "report_status": "FINAL"}, "", "", True)

    assert signed is False
    assert len(withheld) == 3


@pytest.mark.parametrize("t18, uri, summary, reason", [
    (_signed_t18(), "", "narrative", "not rendered to a retrievable URI"),
    (_signed_t18(executive_summary="  "), "minio://t18.json", "narrative",
     "no executive summary"),
    (_signed_t18(), "minio://t18.json", None, "assurance synthesis did not run"),
    (_signed_t18(report_status="PROVISIONAL_PENDING_HITL"), "minio://t18.json",
     "narrative", "pending human review"),
])
def test_each_condition_withholds_the_signature_with_its_reason(t18, uri, summary, reason):
    signed, withheld = signing_status(t18, uri, summary, True)

    assert signed is False
    assert any(reason in r for r in withheld), withheld


def test_a_disclaimer_of_opinion_is_still_signed():
    """ISAE 3000: a disclaimer is a conclusion reached, not a failure to conclude."""
    signed, _ = signing_status(
        _signed_t18(final_verdict="DISCLAIMER_OF_OPINION"), "minio://t18.json",
        "narrative", True)

    assert signed is True


def test_machine_assembled_boilerplate_is_never_signed():
    """The deterministic fallback produces a report; it does not produce an opinion."""
    signed, withheld = signing_status(_signed_t18(), "minio://t18.json", None, True)

    assert signed is False
    assert any("machine-assembled" in r for r in withheld)


# --------------------------------------------------------------------------
# The flag reaches the artefacts
# --------------------------------------------------------------------------
def test_a_freshly_built_t18_is_unsigned_until_the_gate_runs():
    t18 = build_t18("eng-01", {}, {"uri": "minio://t17.json"}, "2026-08-21T00:00:00+00:00")

    assert t18["report_signed"] is False
    assert t18["signature_withheld"]


def test_the_report_carries_the_signature_the_t18_carries():
    t18 = {"report_signed": True, "signature_withheld": [], "auditor_opinion": {}}
    report = assemble_report({"final_verdict": "PASS"}, {"uri": "minio://t17.json"},
                             t18, {"uri": "minio://t18.json"},
                             {"renderer": "weasyprint", "json_uri": "minio://r.json"},
                             "An auditor's summary.", "note")

    assert report["report_signed"] is True
    assert report["declaration_verification_delta"]["report_signed"] is True


def test_an_unsigned_t18_cannot_produce_a_signed_report():
    t18 = {"report_signed": False, "signature_withheld": ["the report was not rendered"],
           "auditor_opinion": {}}
    report = assemble_report({"final_verdict": "PASS"}, {"uri": "minio://t17.json"},
                             t18, {"uri": "minio://t18.json"},
                             {"renderer": "stub", "json_uri": ""}, None, "note")

    assert report["report_signed"] is False
    assert report["declaration_verification_delta"]["signature_withheld"] == [
        "the report was not rendered"]


def test_a_t18_that_never_met_the_gate_is_unsigned_by_default():
    """Absence of the key is not a signature."""
    report = assemble_report({"final_verdict": "PASS"}, {"uri": "minio://t17.json"},
                             {"auditor_opinion": {}}, {"uri": "minio://t18.json"},
                             {"renderer": "stub", "json_uri": ""}, None, "note")

    assert report["report_signed"] is False


@pytest.mark.parametrize("schema_path", [
    "templates/T18_audit_report.json",
    "packages/uagf_tam_templates/src/uagf_tam_templates/schemas/T18_audit_report.json",
])
def test_both_t18_schema_copies_accept_the_signing_fields(schema_path):
    """`additionalProperties: false` — a field the renderer cannot validate fails the run."""
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))

    assert schema["properties"]["report_signed"]["type"] == "boolean"
    assert schema["properties"]["signature_withheld"]["type"] == "array"


@pytest.mark.parametrize("signed, withheld", [
    (True, []),
    (False, ["the report was not rendered to a retrievable URI"]),
])
def test_a_signed_or_unsigned_t18_validates_through_the_real_loader(signed, withheld):
    """The schema the renderer actually loads is `templates/`, not the packaged copy."""
    from aaa.tools.template_render.logger import _load_schema, _validate_payload

    ref = {"template_id": "T17_compliance_matrix", "uri": "minio://eng/t17.json",
           "sha256": "0" * 64, "created_at": "2026-08-21T00:00:00+00:00"}
    t18 = build_t18("eng-01", {"stage_a": {}, "hitl_required": False}, ref,
                    "2026-08-21T00:00:00+00:00")
    t18["report_signed"], t18["signature_withheld"] = signed, withheld

    assert not _validate_payload(t18, _load_schema("T18_audit_report"), "T18_audit_report")


def test_phase_6_has_no_retrieval_channel_in_its_prompt():
    """The prompt promised an expansion round Phase 6 never had (rounds=0)."""
    prompt = Path("PROMPT.md").read_text(encoding="utf-8")
    section = prompt[prompt.index("### Agent 9 — Phase 6"):
                     prompt.index("### Agent 10 — UAGF-TAM-L")]

    assert "You have NO retrieval channel" in section
    assert "do NOT emit `retrieval_plan`" in section.replace("Do NOT", "do NOT")
    assert '"report_signed": true' not in section, "the skeleton pre-set the signature"
