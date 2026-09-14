"""A Tier-3 spawn that measured nothing does not report the confidence of one that did.

The privacy, cyber and L-branch spawns hardcoded 0.9 / 0.85 / 0.9, and the L-branch
listed ``ragas_eval: computed`` on runs that scored no answer at all.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aaa.agents.tier3.confidence import DEGRADED_CONFIDENCE, spawn_confidence
from aaa.agents.tier3.privacy_agent import run as privacy_run
from aaa.agents.tier3.uagf_tam_l import run as l_run


class _Store:
    """Stores nothing, finds nothing."""

    def store_artefact(self, engagement_id: str, phase: str, template_id: str,
                       content: dict, agent: str) -> str:
        """Return a URI for the stored artefact."""
        return f"minio://t/{engagement_id}/{phase}/{template_id}.json"

    def get_artefact(self, uri: str) -> None:
        """Nothing is stored."""
        return None


class _Agent:
    name = "Spawn"
    store = _Store()


async def _no_llm(*_args: Any) -> tuple[str | None, str]:
    return None, "[fallback]"


def test_the_degraded_value_is_the_tier2_convention() -> None:
    assert spawn_confidence(0.9, True) == 0.9
    assert spawn_confidence(0.9, False) == DEGRADED_CONFIDENCE == 0.6


def test_an_l_branch_that_scored_nothing_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(l_run, "run_llm_synthesis", _no_llm)
    report = asyncio.run(l_run.run_uagf_tam_l_branch(
        _Agent(), {"phase_id": "PL", "declaration_summary": {
            "engagement_id": "eng", "modality": "llm", "stage_b": {}}}))
    ragas = next(c for c in report["tool_calls"] if c["tool"] == "ragas_eval")
    assert ragas["result"].startswith("not scored:")
    assert report["confidence"] == DEGRADED_CONFIDENCE


def test_a_privacy_deep_dive_with_nothing_to_scan_is_degraded(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(privacy_run, "run_llm_synthesis", _no_llm)
    report = asyncio.run(privacy_run.run_privacy_audit(
        _Agent(), {"phase_id": "Privacy", "declaration_summary": {"engagement_id": "eng"}}))
    assert report["tool_calls"] == [{"tool": "pii_scan", "result": "skipped"}]
    assert report["confidence"] == DEGRADED_CONFIDENCE


def test_a_named_vector_store_manifest_does_not_take_the_l_branch_down() -> None:
    """Case 04's manifest names its store and model; the reader assumed nested objects."""
    from aaa.agents.tier3.uagf_tam_l.control_sources import _retrieval
    from aaa.agents.tier3.uagf_tam_l.declared_controls import _summary

    case04 = {"version": "2.0", "vector_store": "qdrant",
              "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
              "retrieval_config": {"top_k": 8, "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2"}}
    summary = _retrieval(case04)
    assert summary["vector_store_engine"] == "qdrant"
    assert summary["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert summary["reranker"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    case06 = {"embedding": {"provider": "third_party_hosted_api", "dimensions": 768},
              "vector_store": {"engine": "postgresql_with_vector_extension"}}
    assert _retrieval(case06)["embedding_dimensions"] == 768
    assert _summary("retrieval", ["not", "an", "object"], _retrieval)["unreadable"]
