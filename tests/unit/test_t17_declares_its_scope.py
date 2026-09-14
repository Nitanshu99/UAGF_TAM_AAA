"""Fix 29 (Q5, Q1) — T17 declares the scope it was contracted to assess.

`in_scope_articles` was `sorted(compliance_matrix.keys())` — whatever the matrix
happened to hold — while the schema said the field comes from
`regulatory_coverage.ARTICLE_SET` and KPI 2 counted against that set. The
delivered document therefore presented a 13-article audit as complete beside a
coverage figure of 73.3 % computed over 15.

Emitting a row for every in-scope article is also the second line of defence
behind fix 26: Q1's four articles vanished because one gate did not cover a
verdict, and a table that prints only what it was handed cannot show a reader
what it was never handed.
"""
from __future__ import annotations

from typing import Any

import pytest

from aaa.agents.tier2.report_architect.t17 import build_t17
from aaa.agents.tier2.report_architect.t17_rows import UNREACHED_RATIONALE
from aaa.tools.regulatory_coverage import covered_articles
from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET

NOW = "2026-09-02T00:00:00Z"

#: The matrix as case 01 delivered it — Art. 12, Art. 14, Art. 43 and Art. 72 absent.
DELIVERED_MATRIX: dict[str, str] = {
    "Annex_III": "PASS", "Annex_IV": "PASS", "Art.10": "FAIL",
    "Art.10§2(f)": "FAIL", "Art.11": "PASS", "Art.13": "PASS", "Art.15": "FAIL",
    "Art.15§1": "FAIL", "Art.17": "PASS", "Art.5": "PASS", "Art.50": "PASS",
    "Art.6": "PASS", "Art.9": "PASS",
}


def _decl(**over: Any) -> dict[str, Any]:
    decl: dict[str, Any] = {
        "risk_tier": "high", "is_llm_or_agentic": False,
        "compliance_matrix": dict(DELIVERED_MATRIX), "article_evidence": {},
        "regulatory_coverage_pct": 73.3, "final_verdict": "FAIL",
    }
    decl.update(over)
    return decl


def _rows(t17: dict[str, Any]) -> dict[str, str]:
    return {row["article"]: row["verdict"] for row in t17["articles"]}


# ── the declared scope ───────────────────────────────────────────────────────

def test_scope_comes_from_the_article_set_not_from_the_matrix():
    """Q5 itself: 13 declared beside a KPI computed over 15."""
    t17 = build_t17("eng-01", _decl(), NOW)

    assert t17["in_scope_articles"] == sorted(ARTICLE_SET["high"])
    assert len(t17["in_scope_articles"]) == 14


def test_the_declared_scope_is_the_one_kpi_2_counts_against():
    """The article list and the percentage beside it must describe one audit."""
    state = {"risk_tier": "high", "is_llm_or_agentic": False,
             "compliance_matrix": dict(DELIVERED_MATRIX)}
    t17 = build_t17("eng-01", _decl(), NOW)

    assert t17["in_scope_articles"] == covered_articles(state)["in_scope"]


def test_an_llm_engagement_declares_the_gpai_articles():
    t17 = build_t17("eng-01", _decl(is_llm_or_agentic=True), NOW)

    assert "GPAI_51" in t17["in_scope_articles"]
    assert t17["in_scope_articles"] == sorted(ARTICLE_SET["high_llm"])


# ── a row per in-scope article ───────────────────────────────────────────────

@pytest.mark.parametrize("article", ["Art.12", "Art.14", "Art.43", "Art.72"])
def test_an_article_the_matrix_never_reached_still_gets_a_row(article):
    """The four the delivered conformity table omitted entirely (Q1)."""
    rows = _rows(build_t17("eng-01", _decl(), NOW))

    assert rows[article] == "INSUFFICIENT_EVIDENCE"


def test_an_unreached_article_says_it_was_not_assessed():
    """Not the same statement as 'assessed, could not conclude'."""
    row = next(r for r in build_t17("eng-01", _decl(), NOW)["articles"]
               if r["article"] == "Art.12")

    assert row["rationale"] == UNREACHED_RATIONALE
    assert row["evidence_uris"] == [] and row["supporting_template_ids"] == []


def test_every_in_scope_article_has_exactly_one_row():
    t17 = build_t17("eng-01", _decl(), NOW)
    articles = [row["article"] for row in t17["articles"]]

    assert set(t17["in_scope_articles"]) <= set(articles)
    assert len(articles) == len(set(articles))


def test_the_sub_articles_the_matrix_holds_keep_their_rows():
    """`Art.10§2(f)` is not in ARTICLE_SET and carries a real fairness verdict."""
    rows = _rows(build_t17("eng-01", _decl(), NOW))

    assert rows["Art.10§2(f)"] == "FAIL"
    assert rows["Art.15§1"] == "FAIL"
    assert len(rows) == 17          # the 15 in scope, plus the two sub-articles


def test_a_verdict_the_matrix_holds_is_never_overwritten():
    rows = _rows(build_t17("eng-01", _decl(), NOW))

    for article, verdict in DELIVERED_MATRIX.items():
        assert rows[article] == verdict


def test_evidence_and_findings_still_reach_the_row_that_has_them():
    decl = _decl(article_evidence={"Art.10": {
        "evidence_uris": [f"minio://e/{i}" for i in range(9)],
        "supporting_template_ids": ["T06_datasheet_for_datasets"],
        "rationale": "Two material fairness findings.",
        "finding_ids": ["P4-FAIR-AGE"], "cgsa_control_ids": ["C-1"]}})
    row = next(r for r in build_t17("eng-01", decl, NOW)["articles"]
               if r["article"] == "Art.10")

    assert len(row["evidence_uris"]) == 5          # still capped
    assert row["blocking_findings"] == ["P4-FAIR-AGE"]
    assert row["rationale"] == "Two material fairness findings."


def test_t17_validates_against_its_own_schema():
    from aaa.tools.template_render.logger import _load_schema, _validate_payload

    t17 = build_t17("eng-01", _decl(), NOW)

    assert _validate_payload(t17, _load_schema("T17_compliance_matrix"),
                             "T17_compliance_matrix") == []


def test_a_complete_matrix_gains_nothing_it_did_not_earn():
    """The fix adds rows for gaps; it must not invent verdicts where none is due."""
    full = {a: "PASS" for a in ARTICLE_SET["high"]}
    t17 = build_t17("eng-01", _decl(compliance_matrix=full), NOW)

    assert set(_rows(t17).values()) == {"PASS"}
    assert len(t17["articles"]) == 14
