"""aaa.observability.metrics — Prometheus metrics registry.

Exposes a single global Prometheus ``CollectorRegistry`` with counters and
histograms for:

  - LLM call volume, latency, token usage
  - Phase execution latency
  - Error counts by component

Import individual metrics where you need them::

    from aaa.observability.metrics import LLM_CALL_COUNTER, LLM_LATENCY_HISTOGRAM

The FastAPI ``/metrics`` endpoint (added by ``aaa.api.routes.health``) serves
the text exposition format for Prometheus scraping. It renders
:func:`exposition_registry`, which merges every process's values when
``PROMETHEUS_MULTIPROC_DIR`` is set (see :mod:`~aaa.observability.metrics.multiproc`)."""
from aaa.observability.metrics.error_counter import ENGAGEMENT_COUNTER, ERROR_COUNTER  # noqa: F401
from aaa.observability.metrics.llm_call_counter import (  # noqa: F401
    LLM_CALL_COUNTER,
    LLM_COST_COUNTER,
    LLM_LATENCY_HISTOGRAM,
    LLM_TOKEN_COUNTER,
    PHASE_COUNTER,
    PHASE_LATENCY_HISTOGRAM,
)
from aaa.observability.metrics.multiproc import exposition_registry  # noqa: F401

__all__ = [
    'LLM_CALL_COUNTER',
    'LLM_LATENCY_HISTOGRAM',
    'LLM_TOKEN_COUNTER',
    'LLM_COST_COUNTER',
    'PHASE_LATENCY_HISTOGRAM',
    'PHASE_COUNTER',
    'ERROR_COUNTER',
    'ENGAGEMENT_COUNTER',
    'exposition_registry',
]
