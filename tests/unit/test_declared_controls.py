"""The guardrail configuration and RAG manifest must actually be read.

Both are Annex IV conditional documents: the wizard asks for them, the 80 %
completeness gate counts them, the report lists them by name — and until
2026-09-11 neither was ever passed to ``load_artifact_from_uri``. Case 06's
guardrail configuration declares four of its own controls *not yet implemented*,
including the injection detection the L-branch probes, and the audit had been
inferring that gap instead of reading it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from aaa.agents.tier3.uagf_tam_l.control_status import control_status
from aaa.agents.tier3.uagf_tam_l.declared_controls import resolve_declared_controls

DOCS = Path("mock/06_mariposa_edu_gmbh/docs")


class _Store:
    """Evidence store stub returning one payload per URI."""

    def __init__(self, payloads: dict[str, Any]) -> None:
        self._payloads = payloads

    def get_artefact(self, uri: str) -> Any:
        """Return the payload registered for *uri*."""
        return self._payloads[uri]


@pytest.fixture(name="stage_b")
def _stage_b(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Stage B pointing at the two real case-06 documents."""
    payloads = {
        "minio://e/guardrails.json": json.loads(
            (DOCS / "guardrail_config.json").read_text("utf-8")),
        "minio://e/rag.json": json.loads(
            (DOCS / "rag_manifest.json").read_text("utf-8")),
    }
    monkeypatch.setattr(
        "aaa.platform.artifact_loader.load_artifact_from_uri",
        lambda uri, store, kind=None: payloads[uri])
    return {"guardrail_config_uri": "minio://e/guardrails.json",
            "rag_manifest_uri": "minio://e/rag.json"}


@pytest.mark.skipif(not DOCS.is_dir(), reason="mock bundle not present")
def test_the_unimplemented_controls_the_client_declared_are_surfaced(
        stage_b: dict) -> None:
    """The four case 06 states outright, injection detection among them."""
    declared = resolve_declared_controls(stage_b, _Store({}))
    absent = declared["guardrails"]["declared_not_implemented"]
    assert "input_guardrails.prompt_injection_detection" in absent
    assert len(absent) == 4
    assert declared["guardrails"]["implemented"]
    assert "not enforced programmatically" in declared["guardrails"]["provider_note"]


@pytest.mark.skipif(not DOCS.is_dir(), reason="mock bundle not present")
def test_the_retrieval_configuration_is_read(stage_b: dict) -> None:
    """Enough of the manifest to say what was audited."""
    retrieval = resolve_declared_controls(stage_b, _Store({}))["retrieval"]
    assert retrieval["retrieval_type"] == "two_stage_filter_then_rank"
    assert retrieval["embedding_dimensions"] == 768
    # The manifest says this path has no generative component; the audit should
    # carry that rather than assume an LLM sits in the ranking loop.
    assert retrieval["generative_component_in_path"] is False


def test_nothing_supplied_resolves_to_nothing() -> None:
    """No documents, no invented evidence."""
    assert resolve_declared_controls({}, _Store({})) is None


def test_an_unreadable_document_is_not_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evidence is best-effort; the phase must still run."""
    def _boom(*_a: object, **_k: object) -> Any:
        raise OSError("gone")
    monkeypatch.setattr(
        "aaa.platform.artifact_loader.load_artifact_from_uri", _boom)
    assert resolve_declared_controls(
        {"guardrail_config_uri": "minio://e/x.json"}, _Store({})) is None


@pytest.mark.parametrize("block,expected", [
    ({"implementation_status": {"not_implemented": ["a"]}}, ["a"]),
    ({"implementation_status": {"not_yet_implemented": ["a"]}}, ["a"]),
    ({"status": {"planned": ["a"]}}, ["a"]),
    ({}, []),
])
def test_the_common_spellings_of_the_status_block_are_accepted(
        block: dict, expected: list) -> None:
    """Clients name this block several ways; none of them should be missed."""
    assert control_status(block)["not_implemented"] == expected


def test_t16_carries_the_declared_controls() -> None:
    """The payload, and the narrative input, must both include it."""
    t16_source = Path("aaa/agents/tier3/uagf_tam_l/t16.py").read_text("utf-8")
    llm_source = Path("aaa/agents/tier3/uagf_tam_l/llm.py").read_text("utf-8")
    assert '"declared_controls": declared_controls' in t16_source
    assert '"declared_controls": t16.get("declared_controls")' in llm_source
