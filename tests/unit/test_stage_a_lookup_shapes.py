"""A Stage A field must be readable in every shape a caller holds.

Three Mariposa defects traced to this one split: the composite phase plan fell
back to the scalar modality (Phases 3 and 4 skipped), and the GPAI obligations
stayed in scope for a provider that had declared it places no GPAI model on the
market. In both cases the declaration was present and correct; the reader was
looking in the wrong place. ``t17.py`` even documents the trap — it passes the
*declaration summary*, not the audit state.
"""
from __future__ import annotations

from aaa.platform.state.stage_a_lookup import stage_a_field

_VALUE = [{"id": "matching", "modality": "nlp"}]


def test_top_level_mirror() -> None:
    assert stage_a_field({"component_modalities": _VALUE}, "component_modalities") == _VALUE


def test_declaration_summary_shape() -> None:
    """Phase 6 hands the ReportArchitect ``stage_a`` at the top level."""
    assert stage_a_field({"stage_a": {"component_modalities": _VALUE}},
                         "component_modalities") == _VALUE


def test_audit_state_shape() -> None:
    """The audit state nests it under ``client_submission``."""
    assert stage_a_field({"client_submission": {"stage_a": {"component_modalities": _VALUE}}},
                         "component_modalities") == _VALUE


def test_absent_returns_default() -> None:
    assert stage_a_field({}, "gpai_general_purpose") is None
    assert stage_a_field({}, "gpai_general_purpose", default=True) is True


def test_explicit_false_is_returned_not_treated_as_absent() -> None:
    """``False`` is a declaration, not a missing value — the GPAI case."""
    assert stage_a_field({"stage_a": {"gpai_general_purpose": False}},
                         "gpai_general_purpose", default=True) is False


def test_top_level_wins_over_nested() -> None:
    assert stage_a_field({"modality": "llm", "stage_a": {"modality": "nlp"}}, "modality") == "llm"
