"""Phases 3 and 4 assess the discriminative component, not the system's scalar modality.

Case 06 is a ranker beside an LLM. The planner scheduled P3 and P4 for the ranker,
then the runners dispatched ``modality: llm``, output fairness took the generative
short-circuit, and T11/T12/T13 recorded ``llm`` (T-20260913-010).
"""
from __future__ import annotations

from typing import Any

import pytest

from aaa.agents.tier1.phases.phase_runners.phase import p3, p4
from aaa.tools.csp_solver.catalogue import discriminative_modality


def _state(scalar: str | None, components: list[str] | None = None) -> dict[str, Any]:
    stage_a: dict[str, Any] = {"declared_modality": scalar}
    if components is not None:
        stage_a["component_modalities"] = [{"id": f"c{i}", "modality": m}
                                           for i, m in enumerate(components)]
    return {"engagement_id": "eng-t", "modality": scalar, "declared_modality": scalar,
            "client_submission": {"stage_a": stage_a, "stage_b": {}}}


@pytest.mark.parametrize(("scalar", "components", "expected"), [
    ("llm", ["llm", "nlp"], "nlp"),
    ("llm", None, "llm"),
    ("tabular", None, "tabular"),
    ("llm", ["llm", "agentic"], "llm"),
    (None, None, ""),
])
def test_the_dispatch_modality(scalar: str | None, components: list[str] | None,
                               expected: str) -> None:
    """First discriminative component, else the scalar, else nothing."""
    assert discriminative_modality(_state(scalar, components)) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("runner", [p3, p4])
async def test_the_runner_dispatches_the_discriminative_component(
        monkeypatch: pytest.MonkeyPatch, runner: Any) -> None:
    """What the phase agent is told is ``nlp`` for a composite ranker-plus-LLM."""
    seen: dict[str, Any] = {}

    async def capture(_agent: Any, dispatch: dict, state: dict, **_kw: Any) -> tuple:
        seen.update(dispatch["declaration_summary"])
        return None, state

    monkeypatch.setattr(runner, "run_phase_with_verification", capture)
    monkeypatch.setattr(runner, "_evidence_uris", lambda _state: [])
    run = runner.run_phase_3 if runner is p3 else runner.run_phase_4
    await run(object(), _state("llm", ["llm", "nlp"]))
    assert seen["modality"] == "nlp"
