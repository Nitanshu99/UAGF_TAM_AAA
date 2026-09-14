"""A budget-exhausted audit must not report PASS on phases it never ran."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier1.orchestrator.react.unevidenced import mark_unevidenced, unevidenced_articles


def _state(**overrides: Any) -> dict[str, Any]:
    """Case-02's shape: only Phase 2 ran, four mandatory phases did not."""
    state: dict[str, Any] = {
        "engagement_id": "eng-02-shape",
        "phase_plan": {"P1": "M", "P2": "M", "P3": "O", "P4": "O",
                       "P5": "M", "P6": "M", "L": "S"},
        "phase_artefacts": {
            "T01a_stage_a_triage": {}, "T06_datasheet_for_datasets": {},
            "T07_data_quality_report": {}, "T08_special_category_data_log": {},
        },
    }
    state.update(overrides)
    return state


def test_articles_of_unrun_mandatory_phases_are_reported() -> None:
    """P1 and P5 produced nothing, so their articles are unevidenced.

    Observed on mock case 02, which closed PASS_WITH_OBSERVATIONS having run
    one of six mandatory phases — Art.10 and Art.11 marked passing on evidence
    that was never gathered.
    """
    articles = unevidenced_articles(_state())
    assert "Art.9" in articles, "P5 governance findings never ran"
    assert "Annex_III" in articles, "P1 Annex III mapping never ran"


def test_phase_that_ran_is_not_marked() -> None:
    """Phase 2 produced its artefacts, so Art.10 stays evidenced by them."""
    state = _state()
    produced = set(state["phase_artefacts"])
    assert {"T06_datasheet_for_datasets", "T07_data_quality_report"} <= produced
    # Art.10 is owned solely by P2's templates here, all of which were produced.
    assert "Art.10" not in unevidenced_articles(state)


def test_optional_phases_are_not_required() -> None:
    """An optional phase that did not run is not a coverage gap."""
    articles = unevidenced_articles(_state())
    assert "Art.10§2(f)" not in articles, "P4 is optional in this plan"


def test_marking_populates_the_matrix_input() -> None:
    """The matrix reads insufficient_evidence_articles; marking must fill it."""
    state = _state()
    newly = mark_unevidenced(state)
    assert newly
    assert set(newly) <= set(state["insufficient_evidence_articles"])


def test_marking_is_idempotent() -> None:
    """A second pass must not duplicate entries."""
    state = _state()
    mark_unevidenced(state)
    first = list(state["insufficient_evidence_articles"])
    assert mark_unevidenced(state) == []
    assert state["insufficient_evidence_articles"] == first


def test_fully_covered_run_marks_nothing() -> None:
    """An audit that ran every mandatory phase degrades no article."""
    state = _state(phase_plan={"P2": "M"})
    assert unevidenced_articles(state) == []
