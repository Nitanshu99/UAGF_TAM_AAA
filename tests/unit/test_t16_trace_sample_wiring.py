"""build_t16 must thread a resolved trace_sample into trajectory_audit.

Regression test for the dead-field bug: decl.get("trace_sample", []) was
never populated by any producer, so every agentic engagement's T16
trajectory_audit silently reported zero trajectories forever.
"""
from __future__ import annotations

from aaa.agents.tier3.uagf_tam_l.t16 import build_t16

_DECL = {"stage_c": {}, "stage_b": {"tool_inventory": ["search"]}}
_TRACES = [{"id": "t1", "steps": [{"type": "tool_call", "tool_name": "search", "depth": 1}]}]


def test_agentic_modality_with_trace_sample_reports_real_trajectories():
    """A supplied trace_sample flows through to a non-zero trajectory_audit result."""
    t16 = build_t16(_DECL, "eng-1", "agentic", [], [], [], [], trace_sample=_TRACES)
    assert t16["trajectory_audit"]["total_trajectories"] == 1


def test_agentic_modality_without_trace_sample_is_honestly_zero():
    """No evidence supplied → the zero-trajectory result, not a fabricated pass."""
    t16 = build_t16(_DECL, "eng-1", "agentic", [], [], [], [], trace_sample=None)
    assert t16["trajectory_audit"]["total_trajectories"] == 0


def test_non_agentic_modality_skips_trajectory_audit_entirely():
    """Non-agentic modalities never run trajectory_audit (trajectory stays None)."""
    t16 = build_t16(_DECL, "eng-1", "llm", [], [], [], [], trace_sample=_TRACES)
    assert t16["trajectory_audit"] is None
