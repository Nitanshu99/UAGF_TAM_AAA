"""Prometheus emission for one audited LLM call.

Separate from the record shaping so the audit trail and the dashboards can be
read — and changed — independently. Both are driven by the same call, and
neither is allowed to fail the call.
"""
from __future__ import annotations

from typing import Any


def _emit_metrics(agent_name: str, model: str, status: str, elapsed: float,
                  record: dict[str, Any], response: Any) -> None:
    """Update the call, latency, token and cost series for one call.

    :param agent_name: Originating agent.
    :param model: LiteLLM model string.
    :param status: ``ok`` or ``error``.
    :param elapsed: Wall-clock seconds the call took, across every attempt.
    :param record: The audit record, read for token counts and cost.
    :param response: The LLM response, or ``None`` on failure.
    """
    from aaa.observability.metrics import (
        LLM_CALL_COUNTER,
        LLM_COST_COUNTER,
        LLM_LATENCY_HISTOGRAM,
        LLM_TOKEN_COUNTER,
    )

    LLM_CALL_COUNTER.labels(agent=agent_name, model=model, status=status).inc()
    LLM_LATENCY_HISTOGRAM.labels(agent=agent_name, model=model).observe(elapsed)
    if response is not None:
        for tok_type in ("prompt_tokens", "completion_tokens"):
            LLM_TOKEN_COUNTER.labels(agent=agent_name, model=model,
                                     token_type=tok_type).inc(record.get(tok_type, 0))
        LLM_COST_COUNTER.labels(agent=agent_name, model=model).inc(
            record.get("estimated_cost_usd") or 0.0)


__all__ = ["_emit_metrics"]
