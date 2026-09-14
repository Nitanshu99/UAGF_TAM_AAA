"""Unit tests for the step 4 degraded-run banner (fix F5, finding S3)."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from aaa.ui.wizard.step4 import integrity as banner

# Committed fixture: `data/customer/` is gitignored run output.
_DEGRADED = Path("tests/fixtures/degraded_run/eng-degraded_audit_state.json")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(name="captured")
def _captured(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture what the banner would render, without a Streamlit runtime."""
    messages: list[str] = []

    @contextmanager
    def _expander(label, expanded=False):  # noqa: ARG001
        messages.append(label)
        yield

    monkeypatch.setattr(banner.st, "error", messages.append)
    monkeypatch.setattr(banner.st, "write", messages.append)
    monkeypatch.setattr(banner.st, "expander", _expander)
    return messages


def test_phase_labels_are_human_readable() -> None:
    """A reader of the results page sees phase names, not ids."""
    labels = banner.phase_labels({"degraded_phases": ["P1", "P5"]})
    assert labels == "Phase 1 Scope, Phase 5 Governance"


def test_unknown_phase_id_falls_back_to_itself() -> None:
    """An id outside the label map is shown, not swallowed."""
    assert banner.phase_labels({"degraded_phases": ["P9"]}) == "P9"


def test_clean_run_renders_nothing(captured: list[str]) -> None:
    """A healthy run must not be decorated with an integrity warning."""
    result = banner.render_integrity_banner({"phase_artefacts": {}})
    assert captured == []
    assert result["suitable_for_handoff"] is True


def test_degraded_run_names_the_phases_and_the_count(captured: list[str]) -> None:
    """A degraded run is called out with its phases and its counts."""
    result = banner.render_integrity_banner(_load(_DEGRADED))
    assert result["suitable_for_handoff"] is False
    body = captured[0]
    assert "8 of 19 artefacts are placeholders" in body
    assert "Phase 1 Scope" in body and "Phase 5 Governance" in body
    assert "must not be handed to a client" in body


def test_degraded_run_lists_the_placeholder_artefacts(captured: list[str]) -> None:
    """The reader can see exactly which artefacts are not real."""
    banner.render_integrity_banner(_load(_DEGRADED))
    listing = "\n".join(captured)
    assert "T03_annex_iii_mapping" in listing
    assert "Which 8 artefacts are placeholders?" in listing


def test_a_stamped_block_is_preferred_over_recomputation(captured: list[str]) -> None:
    """The writer's stamp governs, so page and deliverable cannot disagree."""
    state = {"phase_artefacts": {}, "run_integrity": {
        "suitable_for_handoff": False, "stub_artefact_ids": ["T02_system_card"],
        "artefact_count": 1, "degraded_phases": ["P1"], "unwired_agents": ["scope_agent"]}}
    result = banner.render_integrity_banner(state)
    assert result["stub_artefact_ids"] == ["T02_system_card"]
    assert "scope_agent" in captured[0]
