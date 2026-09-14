"""Every gate that used to mean "an OpenAI key" now means "the active provider's key"."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY",
                 "AAA_ORCHESTRATION_MODE", "PROVIDER", "RAGAS_JUDGE_MODEL",
                 "RAGAS_EMBEDDING_MODEL", "OPENROUTER_API_BASE"):
        monkeypatch.delenv(name, raising=False)


def test_react_sequencing_switches_on_with_only_an_openrouter_key(monkeypatch):
    """A fresh clone on one OpenRouter key must not silently fall to graph mode."""
    from aaa.agents.tier1.orchestrator.runner import _react_enabled
    assert _react_enabled() is False
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-x")
    assert _react_enabled() is True


def test_ragas_judge_takes_the_openrouter_route_under_that_provider(monkeypatch):
    """The run's own L-branch model judges, through the gateway with the one key (T-20260914-011)."""
    from aaa.platform.embeddings.openrouter import MODEL as OPENROUTER_EMBEDDING
    from aaa.platform.model_registry.resolve import resolve_model
    from aaa.tools.ragas_eval.compute.judge import _routing, judge_models
    assert _routing() == {}
    assert judge_models() == (resolve_model("UAGF-TAM-L"), "text-embedding-3-small")
    monkeypatch.setenv("PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-x")
    assert _routing() == {"base_url": "https://openrouter.ai/api/v1", "api_key": "sk-or-v1-x"}
    assert judge_models() == ("nvidia/nemotron-3-ultra-550b-a55b:free", OPENROUTER_EMBEDDING)
    assert "gpt-4o-mini" not in judge_models()[0]
    monkeypatch.setenv("RAGAS_JUDGE_MODEL", "openai/gpt-4.1-mini")
    assert judge_models()[0] == "openai/gpt-4.1-mini"


def test_the_ingester_embeds_through_the_regulatory_purpose(monkeypatch):
    """The corpus is written by the embedder that will query it — no direct OpenAI client."""
    import aaa.platform.embeddings as seam
    from scripts.ingest_regulatory_corpus.embed import dense_embed

    calls: list[tuple[list[str], str]] = []

    def fake(texts: list[str], purpose: str) -> list[list[float]]:
        calls.append((texts, purpose))
        return [[0.5] for _ in texts]

    monkeypatch.setattr(seam, "embed_texts", fake)
    assert dense_embed(["one", "two"]) == [[0.5], [0.5]]
    assert calls == [(["one", "two"], "regulatory")]


def test_the_rag_search_path_builds_no_openai_client():
    """An OpenRouter or local embedding host has no OPENAI_API_KEY; the search must not need one."""
    import inspect

    from aaa.agents.tier1.regulatory_rag import clients
    assert "openai.OpenAI" not in inspect.getsource(clients)
