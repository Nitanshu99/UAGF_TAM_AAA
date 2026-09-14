"""Annex III classification rests on the system's own words, down to the sub-point.

The "semantic" score queried the regulatory corpus with the section title, so it
measured the law; declared sections got a flat 0.75; "apprenticeship" and
"recruiters" matched nothing, so a declared §3 was recorded as "no keyword
evidence" (T-20260913-043).
"""
from __future__ import annotations

from aaa.tools.annex_iii_classify import NO_KEYWORD_EVIDENCE, annex_iii_classify, match_term

PURPOSE = ("The service suggests applicants for apprenticeship places. Employer recruiters "
           "review every suggestion and make each hiring decision.")


def _by_section(entries: list) -> dict:
    """Entries keyed by Annex III point."""
    return {e["annex_iii_section"]: e for e in entries}


def test_a_purpose_names_the_sub_points_and_the_words() -> None:
    """§3(a) on "apprenticeship", §4(a) on "recruiters" — both evidenced, both 0.9."""
    entries = _by_section(annex_iii_classify(["3", "4"], PURPOSE))
    assert entries["3"]["use_case_marker"].startswith('§3(a) ')
    assert '"apprenticeship"' in entries["3"]["use_case_marker"]
    assert '"recruiters"' in entries["4"]["use_case_marker"]
    assert entries["3"]["confidence"] == entries["4"]["confidence"] == 0.9


def test_a_declaration_without_supporting_words_is_kept_but_unconfirmed() -> None:
    """A keyword list is no ground to drop a provider's own high-risk declaration."""
    entry = annex_iii_classify(["2"], "anomaly detection on harbour crane telemetry")[0]
    assert entry["provenance"] == "client_declared" and entry["confidence"] == 0.5
    assert entry["use_case_marker"] == NO_KEYWORD_EVIDENCE
    assert "semantic" not in entry["use_case_marker"]


def test_confidence_differs_with_evidence() -> None:
    """Sub-point evidence, section terms only, and nothing are three different claims."""
    assert annex_iii_classify(["3"], "a platform for students")[0]["confidence"] == 0.7
    assert annex_iii_classify(["3"], "exam grading for schools")[0]["confidence"] == 0.9


def test_an_undeclared_section_needs_more_than_a_passing_mention() -> None:
    """One generic word does not add a high-risk section; two terms with a sub-point do."""
    assert not _by_section(annex_iii_classify([], "cv parser reading education history"))
    detected = _by_section(annex_iii_classify([], "credit scoring and loan approval"))
    assert detected["5"]["provenance"] == "phase1_verified" and detected["5"]["confidence"] == 0.7


def test_stems_match_word_forms_and_keep_word_boundaries() -> None:
    """``recruit*`` finds "recruiters"; "face" still does not match inside "HuggingFace"."""
    assert match_term("recruit*", "employer recruiters review") == "recruiters"
    assert match_term("face", "a huggingface model") is None
