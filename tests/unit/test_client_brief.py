"""The client brief — what it may say, and what it is not allowed to say.

The brief is the only deliverable the customer reads unaided, and it is written
by a model. Two properties therefore have to hold whatever the model returns:
the verdicts in it come from the audit state and cannot be moved by prose, and
every requirement the matrix reached appears even when the call for it fails.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier2.client_brief.article_pass import write_article_section
from aaa.agents.tier2.client_brief.bundle import article_bundle, audited_articles
from aaa.agents.tier2.client_brief.fallback import deterministic_section
from aaa.agents.tier2.client_brief.lines import as_lines, bullets
from aaa.agents.tier2.client_brief.markdown import render_brief
from aaa.agents.tier2.client_brief.synthesis import deterministic_overview

_STATE: dict = {
    "engagement_id": "eng-test",
    "final_verdict": "FAIL",
    "auditor_opinion": {"opinion_type": "adverse",
                        "opinion_paragraph": "Not in conformity.",
                        "basis_paragraph": "Confirmed non-conformity on Art.10."},
    "client_submission": {"stage_a": {"provider_name": "Acme GmbH",
                                      "system_name": "Sorter", "version": "2.1",
                                      "special_category_data": False}},
    "compliance_matrix": {"Art.10": "FAIL", "Art.5": "PASS",
                          "Art.12": "INSUFFICIENT_EVIDENCE"},
    "declaration_verification": {"special_category_data": "mismatch",
                                 "risk_tier": "match"},
    "article_evidence": {"Art.10": {"rationale": "PII scan contradicts the declaration.",
                                    "evidence_uris": [], "supporting_template_ids": []}},
    "blocking_findings": [
        {"finding_id": "P2-SPECIAL-CAT", "eu_ai_act_articles": ["Art.10"],
         "description": "Undeclared special-category data found.",
         "materiality": "material", "declared": "special_category_data: false",
         "observed": "nationality and region columns present",
         "recommendation": "Re-declare and document the lawful basis."},
        {"finding_id": "P3-OTHER", "eu_ai_act_articles": ["Art.15"],
         "description": "Unrelated.", "materiality": "observation"},
    ],
    "unadmitted_artefacts": [
        {"template_id": "T06_datasheet_for_datasets", "articles": ["Art.10"],
         "verdict": "escalate_hitl", "reason": "Claims no sensitive features."},
    ],
    "cgsa_blocking_findings": [
        {"control_id": "C08", "control_name": "Data governance",
         "eu_ai_act_article": "Article 10", "finding": "Not documented.",
         "remediation_action": "Document the data governance process."},
    ],
    "cgsa_positive_findings": [
        {"control_id": "C29", "control_name": "Human oversight",
         "finding": "Humans make every final decision."},
    ],
    "remediation_roadmap": [{"recommended_action": "Re-run the PII scan."}],
}


def _sections() -> list[dict]:
    """Deterministic sections for every article the matrix reached."""
    return [deterministic_section(article_bundle(a, _STATE, None))
            for a in audited_articles(_STATE)]


# --------------------------------------------------------------------------
# The bundle carries this article's evidence, and only this article's
# --------------------------------------------------------------------------
def test_articles_are_ordered_worst_first():
    """The reader's first question is what is broken, so the worst verdict leads."""
    assert audited_articles(_STATE) == ["Art.10", "Art.12", "Art.5"]


def test_bundle_links_every_evidence_channel_to_its_article():
    """Findings, rejected artefacts and controls all reach the article they were raised against."""
    bundle = article_bundle("Art.10", _STATE, None)
    assert [f["finding_id"] for f in bundle["findings"]] == ["P2-SPECIAL-CAT"]
    assert bundle["rejected_artefacts"][0]["template_id"] == "T06_datasheet_for_datasets"
    assert bundle["governance_controls"][0]["control_id"] == "C08"
    assert bundle["verdict"] == "FAIL"


def test_bundle_for_an_unrelated_article_is_empty_not_borrowed():
    """An article with no findings of its own is not handed another article's."""
    bundle = article_bundle("Art.5", _STATE, None)
    assert bundle["findings"] == []
    assert bundle["rejected_artefacts"] == []


def test_bundle_reports_an_unresolvable_uri_rather_than_dropping_it():
    """A dangling reference is a fact about the evidence chain, not a gap to paper over."""
    state = {**_STATE, "article_evidence": {
        "Art.10": {"evidence_uris": ["minio://gone/x.json"]}}}
    entry = article_bundle("Art.10", state, None)["admitted_evidence"][0]
    assert entry["resolved"] is False and "could not be read" in entry["note"]


# --------------------------------------------------------------------------
# The model writes the explanation; the state states the result
# --------------------------------------------------------------------------
def test_prose_claiming_a_pass_cannot_move_a_failing_verdict():
    """The model writes the explanation; the audit state states the result."""
    sections = _sections()
    sections[0]["headline"] = "Everything here is fully compliant and passes."
    brief = render_brief(_STATE, "eng-test", sections, deterministic_overview(_STATE))
    assert "| Art.10 | Data and data governance | Not met |" in brief
    assert "**Result: Not met (FAIL).**" in brief


def test_every_audited_requirement_reaches_the_document():
    """Nothing the matrix reached may go unmentioned to the customer."""
    brief = render_brief(_STATE, "eng-test", _sections(), deterministic_overview(_STATE))
    for article in _STATE["compliance_matrix"]:
        assert article in brief


def test_unassessed_requirements_are_not_worded_as_failures():
    """'Could not be checked' is a different fact from 'not met', with a different remedy."""
    brief = render_brief(_STATE, "eng-test", _sections(), deterministic_overview(_STATE))
    assert "| Art.12 | Automatic logging of what the system does | Could not be checked |" in brief


def test_the_brief_reports_strengths_from_the_governance_assessment():
    """What held up is reported with the same evidence as what did not."""
    brief = render_brief(_STATE, "eng-test", _sections(), deterministic_overview(_STATE))
    assert "Humans make every final decision" in brief


# --------------------------------------------------------------------------
# A failed call costs its section's prose, not its section
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_a_failed_call_still_yields_a_grounded_section(monkeypatch):
    """A lost call costs the section its prose, never the section."""
    async def _raise(*_args, **_kwargs):
        raise RuntimeError("provider down")
    monkeypatch.setattr("aaa.agents.tier2.client_brief.article_pass."
                        "acompletion_json_react", _raise)
    section = await write_article_section(object(), article_bundle("Art.10", _STATE, None))
    assert section["llm_written"] is False
    assert section["verdict"] == "FAIL"
    assert any("Undeclared special-category data" in line
               for line in section["what_the_evidence_shows"])


def test_the_deterministic_section_names_the_mismatched_declaration():
    """The fallback still carries the declared-versus-observed contrast it can prove."""
    section = deterministic_section(article_bundle("Art.10", _STATE, None))
    assert any("special_category_data" in line and "mismatch" in line
               for line in section["what_you_told_us"])


def test_the_deterministic_section_does_not_reprint_verified_declarations():
    """Reprinting every verified claim under all seventeen requirements buries the one that matters."""
    section = deterministic_section(article_bundle("Art.10", _STATE, None))
    assert not any("risk_tier" in line for line in section["what_you_told_us"])


# --------------------------------------------------------------------------
# Whatever shape the reply arrives in, it renders
# --------------------------------------------------------------------------
@pytest.mark.parametrize("value,expected", [
    ("one\ntwo", ["one", "two"]),
    (["a", ["b", "c"]], ["a", "b", "c"]),
    (None, []),
    ([], []),
    ({"claim": "you said x"}, ["**claim** — you said x"]),
])
def test_replies_normalise_to_lines(value, expected):
    """A reply renders whether it arrives as prose, a nested list, or a mapping."""
    assert as_lines(value) == expected


def test_empty_content_renders_no_bullet():
    """An absent key leaves no empty bullet behind."""
    assert bullets(None) == "" and bullets([]) == ""
