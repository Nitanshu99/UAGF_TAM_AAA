"""Finding F1/F14 — the regulatory retrieval channel must actually be connected.

The channel was fully built and never plugged in: no entry point constructed a
``RegulatoryRAG``, so ``None`` reached every agent and both retrieval helpers
short-circuited to ``[]`` without a log line.  Every agent's model of the
Regulation collapsed to the partial article list in its static preamble, from
which the Verifier concluded that Art. 72 does not exist (F14).
"""
from __future__ import annotations

import ast
import logging
import pathlib

import pytest

from aaa.agents.tier1.agent_initializer import initialise_agents
from aaa.platform.prompt_registry import load_prompt
from aaa.platform.repo_root import REPO_ROOT
from aaa.tools.evidence_retrieval import seed_regulatory_hits
from aaa.tools.evidence_retrieval.logger import _run_plan_queries

#: Every production entry point that constructs an Orchestrator.
ORCHESTRATOR_CALL_SITES = (
    "aaa/api/routes/workflow/run.py",
    "aaa/cli/cmd/run.py",
    "aaa/ui/wizard/pipeline.py",
)


def _orchestrator_keywords(path: pathlib.Path) -> list[set[str]]:
    """Return the keyword-argument names of each ``Orchestrator(...)`` call."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        {kw.arg for kw in node.keywords if kw.arg}
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Orchestrator"
    ]


@pytest.mark.parametrize("relpath", ORCHESTRATOR_CALL_SITES)
def test_every_entry_point_passes_a_regulatory_rag(relpath):
    calls = _orchestrator_keywords(REPO_ROOT / relpath)
    assert calls, f"no Orchestrator(...) call found in {relpath}"
    for keywords in calls:
        assert "regulatory_rag" in keywords, (
            f"{relpath} builds an Orchestrator without regulatory_rag; agents "
            "would run with no retrieved law (F1)")


def test_build_regulatory_rag_returns_a_searchable_agent():
    from aaa.agents.tier1.regulatory_rag import build_regulatory_rag

    rag = build_regulatory_rag()
    assert rag is not None
    assert callable(rag.search)


def test_initialise_agents_threads_the_rag_to_every_retrieving_agent():
    sentinel = object()
    agents = initialise_agents(evidence_store=object(), regulatory_rag=sentinel)
    retrieving = ("scope_agent", "data_auditor", "model_validator",
                  "output_fairness", "governance_agent")
    for name in retrieving:
        assert agents[name] is not None, f"{name} failed to construct"
        assert agents[name].rag is sentinel, f"{name} did not receive the RAG"


def test_seed_regulatory_hits_logs_an_error_when_the_rag_is_missing(caplog):
    with caplog.at_level(logging.ERROR):
        assert seed_regulatory_hits(None, "Article 10 data governance") == []
    assert any(r.levelno >= logging.ERROR for r in caplog.records), (
        "an unwired RegulatoryRAG must not fail silently (F1)")


def test_plan_queries_log_an_error_when_the_rag_is_missing(caplog):
    plan = {"regulatory_queries": ["Article 72 post-market monitoring"],
            "client_doc_queries": []}
    with caplog.at_level(logging.ERROR):
        reg_q, _, new_reg, _ = _run_plan_queries(plan, None, "")
    assert reg_q and not new_reg
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


def test_seed_regulatory_hits_warns_on_an_empty_result(caplog):
    class _EmptyRag:
        def search(self, query, top_k=3):
            return []

    with caplog.at_level(logging.WARNING):
        assert seed_regulatory_hits(_EmptyRag(), "Article 10") == []
    assert any("no passages" in r.getMessage() for r in caplog.records)


def test_framework_block_declares_itself_a_partial_index():
    """F14: the Verifier denied Art. 72 because it was absent from this list."""
    prompt = load_prompt("verifier")
    assert "PARTIAL INDEX" in prompt
    assert "72" in prompt


def test_verifier_is_not_told_to_confirm_existence_against_the_static_block():
    prompt = load_prompt("verifier")
    assert "Confirm the article exists in the REGULATORY FRAMEWORK block" not in prompt
