"""Shared fakes for the Orchestrator ReAct loop tests."""
from __future__ import annotations

from typing import Any


class FakeOrchestrator:
    """Replays queued decision payloads; snapshots history length per call."""

    def __init__(self, replies: list[dict[str, Any]]):
        self._replies = list(replies)
        self.history_lengths: list[int] = []

    async def acompletion_json(self, prompt_name: str, payload: Any,
                               **_: Any) -> dict[str, Any]:
        """Return the next scripted decision payload."""
        assert prompt_name == "orchestrator"
        self.history_lengths.append(len(payload["decision_history"]))
        return self._replies.pop(0)


def stub_runners(order: list[str]) -> dict[str, Any]:
    """Build a RUNNERS-shaped dict whose runners record their call order.

    Each stub emits the phase's canonical artefact name so the mandatory-phase
    coverage guard sees the same evidence a real runner would produce.
    """
    from aaa.agents.tier1.orchestrator.react.coverage import PHASE_ARTEFACT

    async def make(tag: str, state: dict) -> dict:
        order.append(tag)
        name = PHASE_ARTEFACT.get(tag, f"T_{tag}")
        state.setdefault("phase_artefacts", {})[name] = {"uri": f"minio://{tag}"}
        return state
    return {pid: (lambda a, s, t=pid: make(t, s))
            for pid in ("P1", "P2", "P3", "P4", "P5", "P6", "L", "CYBER", "PRIVACY")}
