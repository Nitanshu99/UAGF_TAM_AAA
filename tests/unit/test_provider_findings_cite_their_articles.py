"""A Verifier provider finding reaches only the articles it names (T-20260914-034, case 06)."""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.provider_findings.cited import cited_articles
from aaa.agents.tier1.verifier.issues import _normalise_issues

T14 = ["Art.9", "Art.14", "Art.17"]


def test_an_article_list_in_prose_is_read_whole() -> None:
    """"Articles 9, 10, 13, 15, and 17" on T14 is Art. 9 and Art. 17 — never Art. 14."""
    issue = {"description": "The provider has not produced the governing artefacts required by "
                            "Articles 9, 10, 13, 15, and 17 for a high-risk system."}
    assert cited_articles(issue, T14) == ["Art.9", "Art.17"]


def test_paragraph_references_map_to_the_template_ids() -> None:
    """Art. 72(1) is Art.72 on T15; Art. 10(2)(f) is the sub-paragraph where the template has it."""
    t15 = {"description": "Performance monitoring (Art. 72(1) read with Art. 15) is not operating; "
                          "the Art. 73 process is documented."}
    assert cited_articles(t15, ["Art.12", "Art.72"]) == ["Art.72"]
    bias = {"description": "Art. 10(2)(f) examination is missing."}
    assert cited_articles(bias, ["Art.10", "Art.10§2(f)"]) == ["Art.10§2(f)"]


def test_an_explicit_list_wins_and_silence_keeps_the_template() -> None:
    """The Verifier's own ``articles`` field decides; an issue naming nothing keeps every article."""
    assert cited_articles({"articles": ["Art.14"], "description": "Art. 9"}, T14) == ["Art.14"]
    assert cited_articles({"description": "No retention period is stated."}, T14) == T14


def test_the_articles_field_survives_normalisation() -> None:
    """The issue key is kept when the model emits it."""
    [issue] = _normalise_issues([{"description": "x", "issue_type": "evidence_gap",
                                  "articles": ["Art.12"]}])
    assert issue["articles"] == ["Art.12"]
