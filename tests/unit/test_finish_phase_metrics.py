"""_finish_phase() must record PHASE_COUNTER/PHASE_LATENCY_HISTOGRAM."""
from __future__ import annotations

import time

from aaa.agents.tier1.phases.verification.finish_phase import _finish_phase
from aaa.observability.metrics import PHASE_COUNTER, PHASE_LATENCY_HISTOGRAM


def test_finish_phase_increments_counter_and_observes_latency():
    """A normal-verdict phase increments the counter and records latency."""
    label = "Phase 3 ModelValidator (test)"
    before = PHASE_COUNTER.labels(phase=label, verdict="pass")._value.get()
    before_count = PHASE_LATENCY_HISTOGRAM.labels(phase=label)._sum.get()

    state: dict = {}
    _finish_phase(state, "pass", rerun_count=0, phase_label=label, t_phase=time.monotonic())

    after = PHASE_COUNTER.labels(phase=label, verdict="pass")._value.get()
    after_sum = PHASE_LATENCY_HISTOGRAM.labels(phase=label)._sum.get()
    assert after == before + 1
    assert after_sum >= before_count
    assert "hitl_required" not in state


def test_finish_phase_flags_hitl_on_escalation():
    """An escalate_hitl verdict still records metrics and flags HITL."""
    label = "Phase 4 OutputFairnessTester (test)"
    state: dict = {}
    _finish_phase(state, "escalate_hitl", rerun_count=2, phase_label=label,
                 t_phase=time.monotonic())
    assert state["hitl_required"] is True
    assert "escalate_hitl" in state["hitl_reason"]
