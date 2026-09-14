"""Fix 50 — a citation may not exceed the artefact's contract (R15 residual).

`_collect_admitted_articles` took the **union** of an artefact's citations and its
contract, so a citation could admit an article nobody had asked that artefact
about. A critique written before fix 47 still admits `Art.15§1` from an output
sampling log whose contract is `Art.10§2(f)`.

Applying it required the contract to be *one thing first*: three declarations of
it — the phase runners, `compliance_matrix._TEMPLATE_ARTICLES` and
`node_stubs.TEMPLATE_ARTICLES` — disagreed in seven places, and restricting
against an incomplete one would have deleted legitimate evidence.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from aaa.agents.tier1.phases.compliance_matrix import _TEMPLATE_ARTICLES
from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.node_stubs.logger import TEMPLATE_ARTICLES
from aaa.tools.regulatory_coverage.artefact_contract import ARTEFACT_ARTICLES, contract_for

T13, T16, T09 = ("T13_output_sampling_log", "T16_uagf_tam_l_evidence", "T09_model_card")


def _state(tid: str, citations: list[str]) -> dict:
    return {"engagement_id": "eng-t",
            "phase_artefacts": {tid: {"uri": f"minio://x/{tid}"}},
            "verifier_critiques": {tid: {"verdict": "accept",
                                         "article_citations": citations}}}


# --------------------------------------------------------------------------- #
# one contract, and it is the runners'
# --------------------------------------------------------------------------- #

def test_the_two_maps_are_now_the_same_object():
    assert _TEMPLATE_ARTICLES is ARTEFACT_ARTICLES
    assert TEMPLATE_ARTICLES is ARTEFACT_ARTICLES


def test_every_phase_runners_contract_matches_the_map():
    """The runners are the authority; the map is their union. They cannot drift."""
    runners = Path("aaa/agents/tier1/phases/phase_runners")
    checked = 0
    for path in sorted((runners / "phase").glob("p[1-6].py")) + [runners / "uagf_tam_l.py"]:
        src = path.read_text()
        if "tid_articles={" not in src:
            continue
        body, depth, out = src.split("tid_articles={", 1)[1], 1, ""
        for ch in body:
            depth += (ch == "{") - (ch == "}")
            if depth == 0:
                break
            out += ch
        for tid, articles in ast.literal_eval("{" + re.sub(r"#[^\n]*", "", out) + "}").items():
            assert sorted(articles) == sorted(ARTEFACT_ARTICLES[tid]), (
                f"{path.name} declares {tid} -> {articles}, the map says "
                f"{ARTEFACT_ARTICLES[tid]}")
            checked += 1
    assert checked >= 16, "the sweep must actually reach every runner"


def test_every_artefact_the_pipeline_produces_has_a_contract():
    from aaa.agents.tier1.phases.nodes.plan import PHASE_TO_TEMPLATES

    missing = sorted({tid for tids in PHASE_TO_TEMPLATES.values() for tid in tids
                      if tid not in ARTEFACT_ARTICLES})
    assert not missing, f"produced but not accountable for anything: {missing}"


def test_contract_for_reads_through_a_spawn_namespace():
    assert contract_for("T11_robustness_report@cyber") == ["Art.15"]
    assert contract_for("T99_invented") is None


# --------------------------------------------------------------------------- #
# a citation is bounded by it
# --------------------------------------------------------------------------- #

def test_a_stale_citation_no_longer_admits_an_article_the_artefact_never_carried():
    """The case R15's residual was raised for."""
    admitted = _collect_admitted_articles(_state(T13, ["Art.10§2(f)", "Art.15§1"]))
    assert "Art.10§2(f)" in admitted
    assert "Art.15§1" not in admitted


def test_a_citation_within_the_contract_is_kept():
    assert "Art.15" in _collect_admitted_articles(_state(T09, ["Art.15"]))
    assert "Art.13" in _collect_admitted_articles(_state(T09, ["Art.13"]))


def test_the_spelling_reconciliation_still_holds_at_this_boundary():
    """Fix 49 normalises; fix 50 bounds. Both, in that order."""
    admitted = _collect_admitted_articles(_state(T16, ["Art.53"]))
    assert "GPAI_53" in admitted
    assert "Art.53" not in admitted


def test_a_sub_article_is_matched_against_its_parent_in_the_contract():
    admitted = _collect_admitted_articles(_state(T09, ["Art.15§1"]))
    assert "Art.15§1" in admitted, "Art.15 is contracted, so its paragraph is covered"


def test_what_was_refused_is_recorded_not_silently_dropped():
    state = _state(T13, ["Art.15§1", "Art.50"])
    _collect_admitted_articles(state)
    over = {c["article"] for c in state["over_cited_articles"]}
    assert over == {"Art.15§1", "Art.50"}
    assert state["over_cited_articles"][0]["template_id"] == T13
    assert state["over_cited_articles"][0]["contract"] == ["Art.10§2(f)"]


def test_the_record_does_not_stack_on_a_second_pass():
    state = _state(T13, ["Art.15§1"])
    _collect_admitted_articles(state)
    _collect_admitted_articles(state)
    assert len(state["over_cited_articles"]) == 1


def test_an_artefact_with_no_contract_admits_nothing_and_says_so(caplog):
    state = {"engagement_id": "eng-t",
             "phase_artefacts": {"T99_invented": {"uri": "minio://x/T99"}},
             "verifier_critiques": {"T99_invented": {"verdict": "accept",
                                                     "article_citations": ["Art.9"]}}}
    with caplog.at_level("WARNING"):
        admitted = _collect_admitted_articles(state)
    assert "Art.9" not in admitted
    assert any("no entry in ARTEFACT_ARTICLES" in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("tid", sorted(ARTEFACT_ARTICLES))
def test_an_artefact_always_admits_its_own_contract(tid):
    """The contract itself is unconditional; only the citations are bounded."""
    admitted = _collect_admitted_articles(_state(tid, []))
    assert set(ARTEFACT_ARTICLES[tid]) <= admitted
