"""Fix 49 — one spelling for the GPAI obligations (finding R17).

`ARTICLE_SET`, `GATE_ARTICLES`, `ARTICLE_PHASE` and the regulatory corpus itself
key on `GPAI_51`-`GPAI_55`. The L-branch's contracts, and the Verifier's citations
after reading them, said `Art.51`-`Art.55`. Case 04 carried five **admitted, PASS**
rows KPI 2's denominator could not see: coverage read 50.0 % over twenty articles
while fifteen had verdicts.

R17 was raised while applying fix 40, which resolved the alias for its scope test
only — rewriting the delivered id would have moved a high-risk case's KPI inside a
fix whose acceptance was that they do not move. This is that fix.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.phases.compliance_matrix import _TEMPLATE_ARTICLES
from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import _supporting_tids
from aaa.agents.tier1.phases.node_stubs.logger import TEMPLATE_ARTICLES
from aaa.agents.tier2.report_architect.constants import ARTICLE_PHASE
from aaa.tools.regulatory_coverage import covered_articles
from aaa.tools.regulatory_coverage.article_set import ARTICLE_SET
from aaa.tools.regulatory_coverage.gate_articles import GATE_ARTICLES
from aaa.tools.regulatory_coverage.ownership import article_owners
from aaa.tools.regulatory_coverage.unowned import KNOWN_UNOWNED

T16 = "T16_uagf_tam_l_evidence"
GPAI = [f"GPAI_{n}" for n in range(51, 56)]
LEGACY = [f"Art.{n}" for n in range(51, 56)]


def _llm_state(**kw) -> dict:
    return {"engagement_id": "eng-04", "risk_tier": "high", "declared_risk_tier": "high",
            "is_llm_or_agentic": True, "phase_artefacts": {}, "verifier_critiques": {},
            **kw}


# --------------------------------------------------------------------------- #
# every end now spells them the same way
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("article", GPAI)
def test_the_canonical_id_is_the_one_the_corpus_uses(article):
    """`regulatory_rag/kb` keys on GPAI_5x; that settles which spelling wins."""
    from aaa.agents.tier1.regulatory_rag.kb.extended import _KB_EXTENDED

    assert article in ARTICLE_SET["high_llm"]
    assert article in ARTICLE_SET["gpai"]
    assert article in GATE_ARTICLES["is_gpai_systemic"]
    assert ARTICLE_PHASE[article] == "L"
    assert "GPAI_51" in _KB_EXTENDED, "the corpus keys on the canonical id"


@pytest.mark.parametrize("source", [_TEMPLATE_ARTICLES, TEMPLATE_ARTICLES])
def test_both_template_maps_now_agree(source):
    assert set(GPAI) <= set(source[T16])
    assert not set(LEGACY) & set(source[T16])


def test_the_phase_contract_agrees_with_the_maps():
    from pathlib import Path
    src = Path("aaa/agents/tier1/phases/phase_runners/uagf_tam_l.py").read_text()
    contract = src.split("tid_articles={", 1)[1].split("}", 1)[0]
    for article in GPAI:
        assert article in contract
    for legacy in LEGACY:
        assert f'"{legacy}"' not in contract


def test_no_contract_in_the_codebase_still_says_art_51():
    """The sweep, kept as a guard."""
    import re
    from pathlib import Path

    pattern = re.compile(r'"Art\.5[1-5]"')
    offenders = [
        f"{path}:{n}"
        for path in Path("aaa").rglob("*.py")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if pattern.search(line) and "canonical" not in line.lower()
    ]
    assert not offenders, f"legacy GPAI spelling still declared: {offenders}"


# --------------------------------------------------------------------------- #
# the citation boundary — a model may still reach for the treaty numbering
# --------------------------------------------------------------------------- #

def test_a_citation_in_the_old_spelling_still_lands_on_the_canonical_id():
    """A critique written before this fix, replayed, must not admit a ghost."""
    state = _llm_state(
        phase_artefacts={T16: {"uri": "minio://x/T16"}},
        verifier_critiques={T16: {"verdict": "accept",
                                  "article_citations": ["Art.53", "Art.15"]}})
    admitted = _collect_admitted_articles(state)
    assert "GPAI_53" in admitted
    assert "Art.53" not in admitted


def test_the_evidence_list_finds_the_artefact_under_either_spelling():
    state = _llm_state(
        phase_artefacts={T16: {"uri": "minio://x/T16"}},
        verifier_critiques={T16: {"verdict": "accept",
                                  "article_citations": ["Art.54"]}})
    assert _supporting_tids(state, "GPAI_54") == [T16]
    assert _supporting_tids(state, "Art.54") == [T16]


def test_a_canonical_citation_works_too():
    state = _llm_state(
        phase_artefacts={T16: {"uri": "minio://x/T16"}},
        verifier_critiques={T16: {"verdict": "accept",
                                  "article_citations": ["GPAI_55"]}})
    assert "GPAI_55" in _collect_admitted_articles(state)
    assert _supporting_tids(state, "GPAI_55") == [T16]


def test_an_unrelated_article_is_not_rewritten():
    """The alias touches five ids and no others.

    Asserted on `canonical_article` directly rather than through admission,
    because fix 50 now also *bounds* what a citation may admit — that is its
    concern, and this test's is the spelling.
    """
    from aaa.tools.regulatory_coverage.engagement_scope import canonical_article

    for article in ("Art.5", "Art.50", "Art.15", "Art.15§1", "Annex_IV", "Art.9"):
        assert canonical_article(article) == article
    for n in range(51, 56):
        assert canonical_article(f"Art.{n}") == f"GPAI_{n}"


# --------------------------------------------------------------------------- #
# the gap fix 41 had to declare is closed, not re-declared
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("article", GPAI)
def test_the_gpai_obligations_now_have_an_accountable_template(article):
    assert article_owners(article, _TEMPLATE_ARTICLES) == {"L"}
    assert article not in KNOWN_UNOWNED


def test_the_declared_gap_list_shrank_rather_than_grew():
    """An exemption list that only grows is a way of not knowing."""
    assert set(KNOWN_UNOWNED) == {"Art.50", "Art.25", "Art.27", "Annex_XI", "Annex_XII"}


# --------------------------------------------------------------------------- #
# the delivered effect
# --------------------------------------------------------------------------- #

def test_an_admitted_l_branch_artefact_passes_the_gpai_obligations():
    state = _llm_state(
        phase_artefacts={T16: {"uri": "minio://x/T16"}},
        verifier_critiques={T16: {"verdict": "accept",
                                  "article_citations": ["Art.51", "Art.52", "Art.53",
                                                        "Art.54", "Art.55"]}})
    _derive_verdicts(state)
    for article in GPAI:
        assert state["compliance_matrix"][article] == "PASS"
    for legacy in LEGACY:
        assert legacy not in state["compliance_matrix"], "listed twice would be worse"


def test_kpi_2_can_now_see_them():
    """The whole point: five verdicts the denominator could not count."""
    state = _llm_state(
        phase_artefacts={T16: {"uri": "minio://x/T16"}},
        verifier_critiques={T16: {"verdict": "accept",
                                  "article_citations": list(LEGACY)}})
    _derive_verdicts(state)
    kpi = covered_articles(state)
    assert set(GPAI) <= set(kpi["in_scope"])
    assert set(GPAI) <= set(kpi["covered"])


def test_a_non_llm_engagement_is_untouched():
    """GPAI obligations do not bind a plain high-risk system."""
    state = {"engagement_id": "eng-01", "risk_tier": "high", "declared_risk_tier": "high",
             "is_llm_or_agentic": False, "phase_artefacts": {}, "verifier_critiques": {}}
    _derive_verdicts(state)
    assert not set(GPAI) & set(state["compliance_matrix"])
