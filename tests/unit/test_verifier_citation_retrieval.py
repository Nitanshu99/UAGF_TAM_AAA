"""F14's other half — the Verifier can now resolve the citations it judges.

Fix 1 stopped the false *"Art. 72 does not exist"* finding by forbidding the
denial. It did not give the Verifier a way to *confirm* a citation: the five
phase agents got a ``regulatory_rag`` and the agent checking their legal claims
did not, while its own prompt said to "resolve the article against Regulatory
RAG output". These tests cover the channel, its absence, and the wiring that
means a future entry point cannot forget it.
"""
from __future__ import annotations

import ast
import importlib
import json
import logging
import pathlib
from typing import Any

from aaa.agents.tier1.verifier import Verifier
from aaa.agents.tier1.verifier.citations import MAX_CITATIONS, cited_references, retrieve_cited_law
from aaa.agents.tier1.verifier.messages import _build_critique_messages
from aaa.agents.tier1.verifier.truncation import truncate_for_budget
from aaa.platform.prompt_registry import load_prompt

#: Call #036's artefact cited Art. 72 — the citation the run called fictional.
_T18 = {"engagement_id": "eng-01", "articles": ["Art.9", "Art. 10§2(b)", "Art.72"],
        "narrative": "Post-market monitoring per Article 72 and Annex IV."}


class _Rag:
    """Records the queries it is asked, returns one hit per query."""

    def __init__(self, fail: bool = False, empty: bool = False):
        self.queries: list[str] = []
        self._fail, self._empty = fail, empty

    def search(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Stand in for the Qdrant hybrid query."""
        self.queries.append(query)
        if self._fail:
            raise RuntimeError("qdrant down")
        if self._empty:
            return []
        return [{"text": f"Text of {query}.", "article": query, "score": 0.9,
                 "source_uri": f"euaiact://{query.split()[1]}"}]


# --------------------------------------------------------------------------- #
# which references an artefact cites
# --------------------------------------------------------------------------- #

def test_articles_and_annexes_are_both_read_out_of_the_artefact():
    """Scope artefacts cite Annexes as often as Articles."""
    assert cited_references(_T18) == ["Article 9", "Article 10", "Article 72", "Annex IV"]


def test_the_paragraph_pinpoint_is_dropped_so_one_article_is_asked_once():
    """`Art. 10§2(b)` and `Art. 10§3` are one corpus unit, not two."""
    assert cited_references({"a": "Art. 10§2(b)", "b": "Art. 10§3"}) == ["Article 10"]


def test_the_citation_budget_is_bounded_and_keeps_first_appearance():
    """An artefact citing everything is citing most of it in passing."""
    many = {"n": [f"Article {i}" for i in range(1, 20)]}
    refs = cited_references(many)
    assert len(refs) == MAX_CITATIONS
    assert refs[0] == "Article 1"


def test_an_artefact_citing_nothing_asks_for_nothing():
    """No citations means no retrieval — not an empty search."""
    rag = _Rag()
    assert retrieve_cited_law(rag, {"summary": "No legal references here."}) == []
    assert not rag.queries


# --------------------------------------------------------------------------- #
# retrieval
# --------------------------------------------------------------------------- #

def test_the_articles_the_artefact_cites_are_the_articles_retrieved():
    """Driven by the artefact, not by a fixed seed query."""
    rag = _Rag()
    hits = retrieve_cited_law(rag, _T18)
    assert rag.queries == ["Article 9 EU AI Act", "Article 10 EU AI Act",
                           "Article 72 EU AI Act", "Annex IV EU AI Act"]
    assert any("Article 72" in h["text"] for h in hits), "the run's 'fictional' article"


def test_hits_are_deduplicated_and_ranked_by_merge_hits():
    """Fix 9's rule, reused rather than re-implemented."""
    class _Dupe(_Rag):
        def search(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
            return [{"text": "same", "source_uri": "euaiact://Article_10", "score": 0.4},
                    {"text": "best", "source_uri": "euaiact://Article_11", "score": 0.95}]

    hits = retrieve_cited_law(_Dupe(), {"a": "Art. 10", "b": "Art. 11"})
    assert len(hits) == 2, "the same chunk returned twice is injected once"
    assert hits[0]["score"] == 0.95, "best-scoring first"


def test_no_rag_is_reported_at_error_not_swallowed(caplog):
    """F1's lesson: a missing channel is logged, never a silent empty list."""
    with caplog.at_level(logging.ERROR):
        assert retrieve_cited_law(None, _T18) == []
    assert "No RegulatoryRAG wired" in caplog.text
    assert "Article 72" in caplog.text, "the log names the retrieval it dropped"


def test_a_failing_retriever_does_not_fail_the_critique(caplog):
    """A critique must still happen; it just happens without the law."""
    with caplog.at_level(logging.WARNING):
        assert retrieve_cited_law(_Rag(fail=True), _T18) == []
    assert "citation retrieval failed" in caplog.text


def test_a_silent_corpus_is_distinguishable_from_never_asking(caplog):
    """"Asked and got nothing" is the prompt's `minor`/unverified route."""
    with caplog.at_level(logging.INFO):
        assert retrieve_cited_law(_Rag(empty=True), _T18) == []
    assert "returned no passage" in caplog.text


# --------------------------------------------------------------------------- #
# it reaches the model
# --------------------------------------------------------------------------- #

def test_the_retrieved_law_travels_in_the_user_message():
    """Retrieval that does not reach the prompt is F1 with extra steps."""
    hits = retrieve_cited_law(_Rag(), _T18)
    msgs = _build_critique_messages("P6", "T18_audit_report", "{}", [], "", {}, hits)
    payload = json.loads(msgs[1]["content"])["review_request"]
    assert len(payload["regulatory_hits"]) == len(hits)
    assert "Article 72" in json.dumps(payload["regulatory_hits"])


def test_the_field_is_present_even_when_retrieval_returned_nothing():
    """An absent key and an empty list read differently to a model."""
    msgs = _build_critique_messages("P6", "T18_audit_report", "{}", [], "", {})
    assert json.loads(msgs[1]["content"])["review_request"]["regulatory_hits"] == []


def test_truncation_keeps_the_law_it_was_given():
    """The oversized-prompt path rebuilds the message; it must rebuild all of it."""
    hits = retrieve_cited_law(_Rag(), _T18)

    class _Agent:
        model = "gpt-4o-mini"

    _, msgs = truncate_for_budget(_Agent(), "P6", "T18_audit_report", _T18, [],
                                  "", {}, hits)
    assert json.loads(msgs[1]["content"])["review_request"]["regulatory_hits"]


# --------------------------------------------------------------------------- #
# wiring — the F3/F1 failure mode was a parameter nobody supplied
# --------------------------------------------------------------------------- #

def test_the_verifier_accepts_and_keeps_a_rag():
    """It had no such parameter at all, which is what F14 came down to."""
    rag = _Rag()
    assert Verifier(regulatory_rag=rag).rag is rag
    assert Verifier().rag is None, "absence degrades, it does not crash"


def test_the_singleton_adopts_the_first_rag_and_never_drops_it():
    """A caller without the RAG must not disarm the check for later phases."""
    # import_module, not `import … as`: the package re-exports a `logger`
    # *object*, which shadows the submodule of the same name on the parent.
    mod = importlib.import_module("aaa.agents.tier1.phases.verification.logger")
    original, mod._VERIFIER = mod._VERIFIER, None
    try:
        rag = _Rag()
        assert mod._get_verifier(None).rag is None
        assert mod._get_verifier(rag).rag is rag, "adopted when first offered"
        assert mod._get_verifier(None).rag is rag, "a later None never strips it"
    finally:
        mod._VERIFIER = original


def test_every_verifier_construction_site_passes_the_rag():
    """Fix 1's AST guard, applied to the agent fix 1 left out."""
    roots = [pathlib.Path("aaa/agents/tier1/orchestrator/agent.py"),
             pathlib.Path("aaa/agents/tier1/phases/verification/logger.py")]
    for path in roots:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "Verifier"]
        assert calls, f"{path} no longer constructs a Verifier"
        for call in calls:
            assert any(kw.arg == "regulatory_rag" for kw in call.keywords), (
                f"{path}:{call.lineno} constructs a Verifier with no regulatory_rag — "
                "this is exactly how F1 and F14 happened")


def test_the_phase_loop_hands_the_agents_rag_to_the_verifier():
    """The RAG is on the phase agent; the Verifier is fetched beside it."""
    src = pathlib.Path(
        "aaa/agents/tier1/phases/verification/run_phase_with_verification.py"
    ).read_text(encoding="utf-8")
    assert '_get_verifier(getattr(agent, "rag", None))' in src


def test_the_prompt_names_the_channel_it_orders_the_model_to_use():
    """Fix 11's rule: say only what the runtime will honour — and all of it."""
    prompt = load_prompt("verifier")
    assert "regulatory_hits" in prompt, "the rule pointed at a channel it never named"
    assert "partial index" in prompt, "fix 1's guard must survive"
