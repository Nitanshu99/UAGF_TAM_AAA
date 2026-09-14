"""Fix 17 — the pass-A seed reaches what the authored string could not.

Two defects, one per channel, both measured live before this suite was written.

*Regulatory.* The five anchors name thirteen references between them and the
corpus returned **ten**: Phase 1's anchor missed Article 5 and Annex III (and
returned Article 23, which it never asked for), Phase 5's missed Article 9. All
three are articles those phases' artefacts are accountable for. A four-citation
query answered at ``top_k=3`` cannot do otherwise — finding P1 one level up.

*Client-document.* The obvious widening, appending the declaration's terms to
the authored query, was measured on case 04's 49-chunk collection and kept
**0 of 3** of Phase 2's own hits: identity terms dominate a vector query and
collapse every phase onto the same cover pages. Run as a separate query and
merged, the same terms keep 3 of 3 and add engagement-specific chunks.

So the property under test throughout is *additive*: the authored query is
never edited, never replaced, and its hits always survive.
"""
from __future__ import annotations

import logging
import pathlib
from typing import Any

from aaa.agents.tier1.verifier.citations import MAX_CITATIONS
from aaa.agents.tier1.verifier.citations import cited_references as verifier_refs
from aaa.tools.evidence_retrieval import seed as seed_mod
from aaa.tools.evidence_retrieval.engagement import engagement_query, engagement_terms
from aaa.tools.evidence_retrieval.refs import cited_references
from aaa.tools.evidence_retrieval.seed import (
    MAX_ANCHOR_REFS,
    seed_client_doc_hits,
    seed_regulatory_hits,
)

#: Phase 5's authored anchor — the one that dropped Article 9 against the corpus.
_P5_ANCHOR = ("Article 9 risk management Article 17 quality management system "
              "Article 12 record-keeping logging Article 72 post-market monitoring")

#: Case 01's Phase 2 declaration slice, as `run_phase_2` builds it.
_DECL = {"engagement_id": "eng-01_finclear_gmbh", "client_doc_collection": "c",
         "modality": "tabular", "risk_tier": "high", "gdpr_overlap": True,
         "special_category_data": False, "target_column": "credit_risk",
         "stage_b": {"model_type": "sklearn_gradient_boosting_classifier_v2.1",
                     "task_type": "binary_classification",
                     "general_description": "Gradient-boosted tree classifier.",
                     "sensitive_feature_columns": ["personal_status", "age",
                                                   "foreign_worker"]}}


class _Rag:
    """A retriever whose search is deaf to identifiers, like the real one."""

    def __init__(self, lookup_fails: bool = False, search_fails: bool = False,
                 holds: tuple[str, ...] = ()):
        self.searched: list[str] = []
        self.looked_up: list[str] = []
        self._lookup_fails, self._search_fails = lookup_fails, search_fails
        self._holds = holds

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return neighbourhood hits — never the articles the query names."""
        self.searched.append(query)
        if self._search_fails:
            raise RuntimeError("qdrant down")
        return [{"text": "Recital 67 text", "ref": "Recital 67", "score": 0.97,
                 "source_uri": "euaiact://Recital_67"},
                {"text": "Article 23 text", "ref": "Article 23", "score": 0.93,
                 "source_uri": "euaiact://Article_23"}][:top_k]

    def lookup(self, ref: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Exact identifier match, as fix 16 built it."""
        self.looked_up.append(ref)
        if self._lookup_fails:
            raise RuntimeError("scroll failed")
        if self._holds and ref not in self._holds:
            return []
        return [{"text": f"{ref} text", "ref": ref, "score": 1.0, "match": "ref_lookup",
                 "lookup_ref": ref, "source_uri": f"euaiact://{ref.replace(' ', '_')}"}]


def _refs(hits: list[Any]) -> list[str]:
    """The references a hit list carries, in order."""
    return [str(h.get("ref")) for h in hits]


# --------------------------------------------------------------------------- #
# reading the references out of a query
# --------------------------------------------------------------------------- #

def test_an_anchor_names_every_reference_it_cites():
    """P5's anchor names four; the corpus returned three of them."""
    assert cited_references(_P5_ANCHOR) == [
        "Article 9", "Article 17", "Article 12", "Article 72"]


def test_articles_and_annexes_are_both_read_out_of_an_anchor():
    """P1's anchor mixes both, and missed one of each against the corpus."""
    assert cited_references("Article 6 classification high-risk Annex III Article 5 "
                            "prohibited practices Article 43 conformity assessment") == [
        "Article 6", "Article 5", "Article 43", "Annex III"]


def test_an_unlimited_parse_returns_more_than_the_verifier_budget():
    """The cap is the Verifier's policy, not a property of the text."""
    many = " ".join(f"Article {n}" for n in range(1, 12))
    assert len(cited_references(many)) == 11
    assert len(cited_references(many, limit=MAX_CITATIONS)) == MAX_CITATIONS


def test_the_verifier_still_caps_its_own_citation_budget():
    """Moving the parse out must not change what the Verifier retrieves."""
    many = {"a": " ".join(f"Art. {n}" for n in range(1, 12))}
    assert verifier_refs(many) == [f"Article {n}" for n in range(1, MAX_CITATIONS + 1)]


# --------------------------------------------------------------------------- #
# the regulatory seed
# --------------------------------------------------------------------------- #

def test_every_reference_the_anchor_names_is_fetched_by_identifier():
    """The measured defect: 10 of 13 named references came back. Now all four."""
    rag = _Rag()
    hits = seed_regulatory_hits(rag, _P5_ANCHOR)
    assert rag.looked_up == ["Article 9", "Article 17", "Article 12", "Article 72"]
    for ref in rag.looked_up:
        assert ref in _refs(hits)


def test_the_anchor_search_is_run_unedited():
    """Widening is another question, not a longer one (see `engagement`)."""
    rag = _Rag()
    seed_regulatory_hits(rag, _P5_ANCHOR)
    assert rag.searched == [_P5_ANCHOR]


def test_the_searched_hits_survive_the_widening():
    """The Recitals are the half no lookup can reach; they must not be evicted."""
    hits = seed_regulatory_hits(_Rag(), _P5_ANCHOR)
    assert "Recital 67" in _refs(hits)
    assert "Article 23" in _refs(hits)


def test_an_exact_match_outranks_the_neighbourhood():
    """`merge_hits` ranks on score, and a lookup scores 1.0 by construction."""
    hits = seed_regulatory_hits(_Rag(), _P5_ANCHOR)
    assert all(h.get("match") == "ref_lookup" for h in hits[:4])
    assert _refs(hits)[-2:] == ["Recital 67", "Article 23"]


def test_a_reference_the_corpus_does_not_hold_is_simply_absent():
    """An empty lookup is meaningful; it must not fabricate or crash."""
    rag = _Rag(holds=("Article 9",))
    hits = seed_regulatory_hits(rag, _P5_ANCHOR)
    assert _refs(hits).count("Article 9") == 1
    assert "Article 17" not in _refs(hits)


def test_a_retriever_without_lookup_still_seeds_by_search():
    """The widening is an addition; its absence degrades to the old behaviour."""

    class _SearchOnly:
        def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
            return [{"text": "t", "ref": "Recital 67", "score": 0.9}]

    assert _refs(seed_regulatory_hits(_SearchOnly(), _P5_ANCHOR)) == ["Recital 67"]


def test_a_raising_lookup_does_not_fail_the_phase():
    """Retrieval is evidence-gathering; it must never crash an audit phase."""
    hits = seed_regulatory_hits(_Rag(lookup_fails=True), _P5_ANCHOR)
    assert _refs(hits) == ["Recital 67", "Article 23"]


def test_a_raising_search_still_lets_the_lookups_answer():
    """The two retrievals are independent, so one failing is not both failing."""
    hits = seed_regulatory_hits(_Rag(search_fails=True), _P5_ANCHOR)
    assert _refs(hits) == ["Article 9", "Article 17", "Article 12", "Article 72"]


def test_the_lookup_budget_is_bounded():
    """One seed must not become a retrieval storm."""
    rag = _Rag()
    seed_regulatory_hits(rag, " ".join(f"Article {n}" for n in range(1, 12)))
    assert len(rag.looked_up) == MAX_ANCHOR_REFS


def test_an_unwired_retriever_is_reported_not_silently_empty(caplog):
    """F1's condition: no law returned must never look like no law existing."""
    with caplog.at_level(logging.ERROR):
        assert seed_regulatory_hits(None, _P5_ANCHOR) == []
    assert "No RegulatoryRAG wired" in caplog.text


def test_an_empty_anchor_retrieves_nothing():
    """A query built from nothing would return the corpus's arbitrary top."""
    rag = _Rag()
    assert seed_regulatory_hits(rag, "") == []
    assert rag.searched == [] and rag.looked_up == []


# --------------------------------------------------------------------------- #
# what the declaration says this engagement is
# --------------------------------------------------------------------------- #

def test_the_declaration_supplies_the_terms_no_authored_query_carries():
    """The three sensitive columns drive case 01's findings and seeded nothing."""
    terms = engagement_terms(_DECL)
    assert "personal status age foreign worker" in " ".join(terms)
    assert "credit risk" in terms


def test_the_nested_stage_b_is_read_as_well_as_the_top_level():
    """Phase runners hand each agent a different slice; both shapes must work."""
    assert "binary classification" in engagement_terms(_DECL)
    assert "tabular" in engagement_terms(_DECL)


def test_underscored_identifiers_become_words():
    """The dossier says "gradient boosted"; the declaration says the token."""
    assert "sklearn gradient boosting classifier v2.1" in engagement_terms(_DECL)


def test_a_true_flag_becomes_a_phrase_and_a_false_one_says_nothing():
    """A bare `True` retrieves nothing; the claim it stands for retrieves."""
    terms = engagement_terms(_DECL)
    assert "GDPR personal data processing" in terms
    assert not any("special categories" in t for t in terms)


def test_annex_iii_sections_are_named_as_the_regulation_names_them():
    """`["5"]` is not a query; "Annex III point 5" is."""
    assert "Annex III point 5" in engagement_terms({"declared_annex_iii_sections": ["5"]})


def test_a_declaration_describing_nothing_yields_no_query():
    """A dispatch carrying only an id describes no system to ask about."""
    assert engagement_query({"engagement_id": "eng-01"}) == ""
    assert engagement_query({}) == ""


# --------------------------------------------------------------------------- #
# the client-document seed
# --------------------------------------------------------------------------- #

def _stub_search(monkeypatch, results: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Record the queries issued and answer each from *results*."""
    asked: list[str] = []

    def _fake(engagement_id: str, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        asked.append(query)
        return results.get("derived" if "credit risk" in query else "fixed", [])

    monkeypatch.setattr(seed_mod, "client_doc_search", _fake)
    return asked


_FIXED_HITS = [{"text": "golden set", "source_uri": "u/golden", "chunk_index": 0,
                "score": 0.42}]
_DERIVED_HITS = [{"text": "system card", "source_uri": "u/card", "chunk_index": 0,
                  "score": 0.62}]


def test_both_queries_are_asked(monkeypatch):
    """Two questions, not one longer one — the whole of the client-doc half."""
    asked = _stub_search(monkeypatch, {"fixed": _FIXED_HITS, "derived": _DERIVED_HITS})
    seed_client_doc_hits("eng-01", "data governance PII policy", _DECL)
    assert len(asked) == 2
    assert asked[0] == "data governance PII policy"


def test_the_authored_query_is_never_concatenated_with_the_declaration(monkeypatch):
    """Concatenation kept 0 of 3 of this phase's hits on the live collection."""
    asked = _stub_search(monkeypatch, {"fixed": _FIXED_HITS, "derived": _DERIVED_HITS})
    seed_client_doc_hits("eng-01", "data governance PII policy", _DECL)
    assert "data governance PII policy" not in asked[1]


def test_the_authored_query_keeps_all_of_its_hits(monkeypatch):
    """The additive property: widening may add, and may never subtract."""
    _stub_search(monkeypatch, {"fixed": _FIXED_HITS, "derived": _DERIVED_HITS})
    hits = seed_client_doc_hits("eng-01", "data governance PII policy", _DECL)
    assert {h["source_uri"] for h in hits} == {"u/golden", "u/card"}


def test_a_declaration_describing_nothing_asks_only_the_authored_query(monkeypatch):
    """No derived query to run, so the seed is exactly what it always was."""
    asked = _stub_search(monkeypatch, {"fixed": _FIXED_HITS})
    hits = seed_client_doc_hits("eng-01", "data governance PII policy",
                                {"engagement_id": "e"})
    assert asked == ["data governance PII policy"]
    assert len(hits) == 1


def test_no_engagement_means_no_collection_to_search(monkeypatch):
    """"" disables client-doc retrieval throughout the codebase."""
    asked = _stub_search(monkeypatch, {"fixed": _FIXED_HITS})
    assert seed_client_doc_hits("", "data governance", _DECL) == []
    assert asked == []


# --------------------------------------------------------------------------- #
# the label has to be readable by the agent that receives it
# --------------------------------------------------------------------------- #

def test_every_phase_prompt_explains_what_an_exact_match_means():
    """A 1.0 that means *identity* must not be read as *relevance*.

    Fix 16 told the Verifier how to read ``match``; these five agents now
    receive the same labelled hits and need the same rule.
    """
    text = pathlib.Path("PROMPT.md").read_text(encoding="utf-8")
    assert text.count('marked `match: "ref_lookup"` was fetched by') == 5
    assert text.count("not that it is the passage most relevant to your question") == 5


def test_the_phase_prompts_say_an_absent_article_is_absent_from_the_corpus():
    """The reading fix 1 forbade by guesswork is now available by construction."""
    text = pathlib.Path("PROMPT.md").read_text(encoding="utf-8")
    assert text.count("genuinely absent from the corpus, not merely\noutranked.") == 5
