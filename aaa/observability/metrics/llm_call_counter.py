"""Part 1 of the former ``metrics`` module (auto-split)."""
from __future__ import annotations

from prometheus_client import REGISTRY, Counter, Histogram

LLM_CALL_COUNTER: Counter = Counter(
    "aaa_llm_calls_total",
    "Total number of LLM calls made",
    labelnames=["agent", "model", "status"],
    registry=REGISTRY,
)


LLM_LATENCY_HISTOGRAM: Histogram = Histogram(
    "aaa_llm_latency_seconds",
    "LLM call latency in seconds",
    labelnames=["agent", "model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
    registry=REGISTRY,
)


LLM_TOKEN_COUNTER: Counter = Counter(
    "aaa_llm_tokens_total",
    "Total tokens consumed across all LLM calls",
    labelnames=["agent", "model", "token_type"],
    registry=REGISTRY,
)


LLM_COST_COUNTER: Counter = Counter(
    "aaa_llm_cost_usd_total",
    "Estimated cumulative LLM cost in USD",
    labelnames=["agent", "model"],
    registry=REGISTRY,
)


PHASE_LATENCY_HISTOGRAM: Histogram = Histogram(
    "aaa_phase_latency_seconds",
    "Audit phase execution latency in seconds",
    # engagement_id deliberately excluded: an unbounded label value would grow
    # one time series per engagement forever (a Prometheus cardinality
    # anti-pattern) — per-engagement detail already lives in the Langfuse
    # trace / llm_audit.jsonl, keyed by engagement_id there instead.
    labelnames=["phase"],
    buckets=[1.0, 5.0, 15.0, 30.0, 60.0, 180.0, 300.0, 600.0],
    registry=REGISTRY,
)


PHASE_COUNTER: Counter = Counter(
    "aaa_phases_total",
    "Total number of phase executions",
    labelnames=["phase", "verdict"],
    registry=REGISTRY,
)
