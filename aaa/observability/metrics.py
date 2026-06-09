"""
aaa.observability.metrics — Prometheus metrics registry.

Exposes a single global Prometheus ``CollectorRegistry`` with counters and
histograms for:

  - LLM call volume, latency, token usage
  - Phase execution latency
  - Error counts by component

Import individual metrics where you need them::

    from aaa.observability.metrics import LLM_CALL_COUNTER, LLM_LATENCY_HISTOGRAM

The FastAPI ``/metrics`` endpoint (added by ``aaa.api.routes.health``) serves
the text exposition format for Prometheus scraping.
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY


# ---------------------------------------------------------------------------
# LLM call metrics
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Phase / pipeline metrics
# ---------------------------------------------------------------------------

PHASE_LATENCY_HISTOGRAM: Histogram = Histogram(
    "aaa_phase_latency_seconds",
    "Audit phase execution latency in seconds",
    labelnames=["phase", "engagement_id"],
    buckets=[1.0, 5.0, 15.0, 30.0, 60.0, 180.0, 300.0, 600.0],
    registry=REGISTRY,
)

PHASE_COUNTER: Counter = Counter(
    "aaa_phases_total",
    "Total number of phase executions",
    labelnames=["phase", "verdict"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Error metrics
# ---------------------------------------------------------------------------

ERROR_COUNTER: Counter = Counter(
    "aaa_errors_total",
    "Total number of captured errors",
    labelnames=["component", "exception_type"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Engagement metrics
# ---------------------------------------------------------------------------

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
