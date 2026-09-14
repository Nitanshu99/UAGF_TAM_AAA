"""Stage B's data dictionary must resolve from either shape it arrives in.

A CLI intake bundle nests the block; the wizard also writes the same keys at the
top level. Anything reading only the top level works from the UI and silently
sees nothing from a bundle. On 2026-09-10 that shipped a baseline whose S6
hand-off declared ``target_column: None``, ``positive_label: None`` and
``sensitive_feature_columns: []`` for an engagement whose dossier named all
three — and dispatched Phase 2 with the same blanks, after which the Verifier
raised a material non-conformity for a T06 reporting no sensitive features.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aaa.tools.data_dictionary import explicit_data_dictionary

BUNDLE = Path("mock/06_mariposa_edu_gmbh/stage_b.json")

_NESTED = {"data_dictionary": {"target_column": "y", "positive_label": 1,
                               "sensitive_feature_columns": ["age", "sex"]}}
_TOP = {"target_column": "y", "positive_label": 1,
        "sensitive_feature_columns": ["age", "sex"]}


@pytest.mark.parametrize("stage_b", [_NESTED, _TOP, {**_NESTED, **_TOP}],
                         ids=["nested", "top-level", "both"])
def test_all_three_shapes_resolve_the_same(stage_b: dict) -> None:
    """Whichever way a client's dossier arrives, the audit sees the same block."""
    block = explicit_data_dictionary(stage_b)
    assert block["target_column"] == "y"
    assert block["positive_label"] == 1
    assert block["sensitive_feature_columns"] == ["age", "sex"]


def test_an_empty_nested_value_does_not_mask_a_top_level_one() -> None:
    """``{"data_dictionary": {"sensitive_feature_columns": []}}`` is not an answer."""
    stage_b = {"data_dictionary": {"sensitive_feature_columns": []},
               "sensitive_feature_columns": ["age"]}
    assert explicit_data_dictionary(stage_b)["sensitive_feature_columns"] == ["age"]


def test_nothing_declared_resolves_to_nothing() -> None:
    """No invention: an empty dossier stays empty so the caller can say so."""
    block = explicit_data_dictionary({})
    assert block.get("target_column") is None
    assert not block.get("sensitive_feature_columns")


@pytest.mark.skipif(not BUNDLE.is_file(), reason="mock bundle not present")
def test_the_case_06_bundle_resolves_its_declared_columns() -> None:
    """The exact regression: this bundle nests, and used to resolve to nothing."""
    block = explicit_data_dictionary(json.loads(BUNDLE.read_text("utf-8")))
    assert isinstance(block["target_column"], str) and block["target_column"]
    assert block["positive_label"] is not None
    assert len(block["sensitive_feature_columns"]) == 5


def test_the_phase_2_dispatch_reads_the_resolver_not_the_top_level() -> None:
    """Guards the call site, not just the helper."""
    source = Path(
        "aaa/agents/tier1/phases/phase_runners/phase/p2.py").read_text("utf-8")
    assert "explicit_data_dictionary" in source
    assert 'stage_b.get("target_column")' not in source


@pytest.mark.parametrize("path", [
    "aaa/integrations/handoff.py",
    "aaa/integrations/s6_contract/columns.py",
])
def test_the_handoff_surfaces_read_the_resolver(path: str) -> None:
    """The two places that publish these columns to the next system."""
    source = Path(path).read_text("utf-8")
    assert "explicit_data_dictionary" in source
