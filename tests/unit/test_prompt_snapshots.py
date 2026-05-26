"""
Prompt snapshot tests — pin the exact f-string output of every static prompt
builder so refactors that alter the wording become visible in PR diffs.

Why this matters
----------------
The compliance critique relies on the verbatim phrasing of the four-dimension
rubric inside ``_build_critique_prompt``.  Silent edits would change the
behaviour of every Tier-1/2 critique without any test failing.  These tests
intentionally hard-code the expected text; if you need to change a prompt,
update both the builder and the snapshot in the same commit.
"""
from __future__ import annotations

from aaa.agents.tier1.verifier import _build_critique_prompt


_EMPTY_URIS_SNAPSHOT = """You are an independent EU AI Act compliance auditor.
Critique the following artefact on four dimensions:
1. factual_accuracy   – are all claims grounded in the provided evidence URIs?
2. completeness       – are all required sections present and non-empty?
3. evidence_linkage   – does every assertion reference at least one evidence URI?
4. citation_correctness – are all regulatory citations well-formed and in scope?

Phase: P1
Template: T02_system_card

Evidence URIs available:
  (none)

Artefact content:
{"hello": "world"}

Respond ONLY with a JSON object with these keys:
  issues           : list[str]  – blocking issues (empty = no blocking issues)
  notes            : list[str]  – non-blocking observations
  article_citations: list[str]  – EU AI Act article IDs cited in this artefact
                                  (e.g. "Art.9", "Annex_III", "GPAI_51")
"""


_TWO_URIS_SNAPSHOT = """You are an independent EU AI Act compliance auditor.
Critique the following artefact on four dimensions:
1. factual_accuracy   – are all claims grounded in the provided evidence URIs?
2. completeness       – are all required sections present and non-empty?
3. evidence_linkage   – does every assertion reference at least one evidence URI?
4. citation_correctness – are all regulatory citations well-formed and in scope?

Phase: P6
Template: T17_compliance_matrix

Evidence URIs available:
  - evidence://eng-001/p1/T02_system_card.json
  - evidence://eng-001/p3/T11_robustness_report.json

Artefact content:
{"in_scope_articles": ["Art.9", "Art.10"]}

Respond ONLY with a JSON object with these keys:
  issues           : list[str]  – blocking issues (empty = no blocking issues)
  notes            : list[str]  – non-blocking observations
  article_citations: list[str]  – EU AI Act article IDs cited in this artefact
                                  (e.g. "Art.9", "Annex_III", "GPAI_51")
"""


def test_critique_prompt_no_evidence_uris():
    """Empty-URI branch renders the literal '(none)' placeholder."""
    actual = _build_critique_prompt(
        phase_id="P1",
        template_id="T02_system_card",
        content_str='{"hello": "world"}',
        evidence_uris=[],
    )
    assert actual == _EMPTY_URIS_SNAPSHOT


def test_critique_prompt_with_evidence_uris():
    """Two-URI branch renders one '  - <uri>' line per entry, in order."""
    actual = _build_critique_prompt(
        phase_id="P6",
        template_id="T17_compliance_matrix",
        content_str='{"in_scope_articles": ["Art.9", "Art.10"]}',
        evidence_uris=[
            "evidence://eng-001/p1/T02_system_card.json",
            "evidence://eng-001/p3/T11_robustness_report.json",
        ],
    )
    assert actual == _TWO_URIS_SNAPSHOT


def test_critique_prompt_uri_order_is_preserved():
    """The prompt MUST list URIs in the order received (not sorted)."""
    actual = _build_critique_prompt(
        phase_id="P2",
        template_id="T06_datasheet_for_datasets",
        content_str="{}",
        evidence_uris=["evidence://b", "evidence://a", "evidence://c"],
    )
    block = actual.split("Evidence URIs available:\n", 1)[1]
    block = block.split("\n\nArtefact content:", 1)[0]
    assert block == "  - evidence://b\n  - evidence://a\n  - evidence://c"


def test_critique_prompt_contains_four_rubric_dimensions():
    """All four rubric dimensions must be present in any built prompt."""
    actual = _build_critique_prompt("P1", "T02", "{}", [])
    for dim in (
        "factual_accuracy",
        "completeness",
        "evidence_linkage",
        "citation_correctness",
    ):
        assert dim in actual, f"Rubric dimension '{dim}' missing from prompt"


def test_critique_prompt_demands_json_object_response():
    """Response contract must explicitly require a JSON object with 3 keys."""
    actual = _build_critique_prompt("P1", "T02", "{}", [])
    assert "Respond ONLY with a JSON object" in actual
    assert "issues" in actual
    assert "notes" in actual
    assert "article_citations" in actual
