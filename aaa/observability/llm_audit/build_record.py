"""Assembling one audit record: identity, latency, attempts, usage and cost."""
from __future__ import annotations

import time
from typing import Any

from aaa.observability.llm_audit.pricing import resolve_cost
from aaa.observability.llm_audit.record import _extract_text, _extract_usage
from aaa.platform.model_registry.decoding import decoding_kwargs, sent_decoding
from aaa.platform.transient_retry.attempts import retried_so_far, served_model_so_far


def build_record(call: Any, response: Any = None,
                 error: BaseException | None = None) -> dict:
    """Assemble the audit record for this call."""
    elapsed_ms = round((time.perf_counter() - call._start) * 1000, 1)
    # Fix 39 left this writer without `attempts`, which `aaa.agents.base.audit`
    # records on every row — the exact shape drift this module's sibling
    # docstring warns about. It reads the same contextvar rather than taking a
    # parameter, so a caller cannot forget it and a caller outside a recording
    # block correctly gets `attempts: 1`.
    retried = retried_so_far()
    record: dict[str, Any] = {
        "call_id": call.call_id, "engagement_id": call.engagement_id,
        "agent_name": call.agent_name, "model": call.model,
        "messages": call.messages, "latency_ms": elapsed_ms,
        "status": "ok" if error is None else "error",
        "attempts": len(retried) + 1,
        # Same shape as `aaa.agents.base.audit`: request and wire can differ.
        "decoding": {"requested": decoding_kwargs(call.model),
                     "sent": sent_decoding(call.model)}, **call.extra,
    }
    if retried:
        record["retried_after"] = retried
    if served := served_model_so_far():
        record["served_model"] = served
    if response is not None:
        record["response_text"] = _extract_text(response)
        usage = _extract_usage(response)
        record.update(usage)
        # Q9: null when nothing could price it, never 0.0 — see `pricing`.
        cost, basis = resolve_cost(response, call.model, usage)
        record["estimated_cost_usd"] = cost
        record["cost_basis"] = basis
    if error is not None:
        record["error"] = repr(error)
    return record


__all__ = ["build_record"]
