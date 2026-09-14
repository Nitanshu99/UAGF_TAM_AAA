"""T-20260914-010: T02's phase summary states its own fields; the LLM's prose cannot replace it.

Case 04's T02 summary (LLM-written) called the declared modality verified while the
verification map beside it recorded a mismatch; the Verifier gave factual accuracy 0.
"""
from __future__ import annotations

import json
from pathlib import Path

from aaa.agents.tier2.scope_agent.artefacts import build_and_store_artefacts
from aaa.agents.tier2.scope_agent.verify import run_verification

_CASE = Path(__file__).resolve().parents[2] / "mock" / "04_legalmindd_ai_ltd"


class _Store:
    """Keeps what would be stored."""

    def __init__(self) -> None:
        self.saved: dict = {}

    def store_artefact(self, _eid, _phase, tid, payload, _name) -> str:
        """Record *payload* under *tid*."""
        self.saved[tid] = payload
        return f"minio://{tid}"


class _Agent:
    name = "ScopeAgent"

    def __init__(self) -> None:
        self.store = _Store()


def test_case_04_summary_reports_the_modality_mismatch_whatever_the_llm_said() -> None:
    """Declared agentic, verified llm: the summary says so; the contradicting prose is gone."""
    stage_a = json.loads((_CASE / "stage_a.json").read_text())
    stage_b = json.loads((_CASE / "stage_b.json").read_text())
    ctx = run_verification(None, stage_a, stage_b, {"stage_b": stage_b},
                           {"evidence_uris": []}, "eng-04", stage_a["intended_purpose"])
    ctx.update(client_doc_hits=[], evidence_uris=[])
    agent = _Agent()
    build_and_store_artefacts(agent, ctx, "Declared modality agentic verified (match).", "note")
    summary = agent.store.saved["T02_system_card"]["phase1_summary"]
    assert ctx["verification_map"]["modality"] == "mismatch"
    assert "verified 'llm' (mismatch)" in summary and "verified (match)" not in summary
