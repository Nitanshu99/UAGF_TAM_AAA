"""Part 2 of the former ``metrics`` module (auto-split)."""
from __future__ import annotations

from prometheus_client import REGISTRY, Counter

from aaa.observability.metrics.llm_call_counter import (  # noqa: F401
    LLM_CALL_COUNTER,
    LLM_COST_COUNTER,
    LLM_LATENCY_HISTOGRAM,
    LLM_TOKEN_COUNTER,
    PHASE_COUNTER,
    PHASE_LATENCY_HISTOGRAM,
)

ERROR_COUNTER: Counter = Counter(
    "aaa_errors_total",
    "Total number of captured errors",
    labelnames=["component", "exception_type"],
    registry=REGISTRY,
)


ENGAGEMENT_COUNTER: Counter = Counter(
    "aaa_engagements_total",
    "Total number of engagements processed",
    labelnames=["status", "final_verdict"],
    registry=REGISTRY,
)


__all__ = [
    "LLM_CALL_COUNTER",
    "LLM_LATENCY_HISTOGRAM",
    "LLM_TOKEN_COUNTER",
    "LLM_COST_COUNTER",
    "PHASE_LATENCY_HISTOGRAM",
    "PHASE_COUNTER",
    "ERROR_COUNTER",
    "ENGAGEMENT_COUNTER",
]
