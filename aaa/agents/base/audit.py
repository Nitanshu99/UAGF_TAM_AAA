"""Audit-trail and metrics recording for BaseAgent LLM calls.

The JSONL path, the append itself, and the response-field extractors are owned
by :mod:`aaa.observability.llm_audit.record`, and the Prometheus emission by
:mod:`aaa.agents.base.audit_metrics`; this module only builds the BaseAgent
record shape and hands it to both. Both writers previously carried their own
path constant and duplicate extraction logic, which let the record shapes drift
(``agent`` here versus ``agent_name`` there) and meant redirecting the trail
required patching two places.
"""
from __future__ import annotations

import datetime as _dt
import time
from typing import Any

from aaa.agents.base.audit_metrics import _emit_metrics
from aaa.observability.llm_audit.pricing import resolve_cost
from aaa.observability.llm_audit.record import _extract_text, _extract_usage, _write_jsonl
from aaa.platform.model_registry.decoding import decoding_kwargs, sent_decoding
from aaa.platform.transient_retry.attempts import served_model_so_far


def _response_fields(record: dict[str, Any], response: Any) -> None:
    """Copy reply text / usage / cost onto the audit record (best effort).

    :param record: The audit record, mutated in place.
    :type record: dict[str, Any]
    :param response: The LLM response object.
    :type response: Any
    :returns: None
    """
    record["response_text"] = _extract_text(response)
    usage = _extract_usage(response)
    record.update(usage)
    # Q9: null when nothing could price it, never 0.0 — see `llm_audit.pricing`.
    cost, basis = resolve_cost(response, str(record.get("model", "")), usage)
    record["estimated_cost_usd"] = cost
    record["cost_basis"] = basis


def write_audit(agent_name: str, model: str, messages: list, call_id: str, t0: float,
                response: Any = None, error: BaseException | None = None,
                retried: list[str] | None = None) -> None:
    """Append one LLM-call record to the audit JSONL and update metrics.

    :param agent_name: Originating agent.
    :param model: LiteLLM model string.
    :param messages: Full prompt sent to the model.
    :param call_id: UUID of the individual call.
    :param t0: ``time.perf_counter()`` value at call start.
    :param response: The LLM response (on success).
    :param error: The raised exception (on failure).
    :param retried: Repr of each transient failure fix 39 retried past. Always
        recorded as ``attempts`` so a reader can tell a first-attempt success
        (``attempts: 1``) from a recovered one (``attempts: 2``); ``latency_ms``
        spans every attempt, which is what the call actually cost.
    """
    from aaa.observability.trace_context import current_engagement_id
    from aaa.platform.phase_budget import observe

    elapsed = time.perf_counter() - t0
    # Fix 34: every call is already timed here, so this is the whole
    # instrumentation the phase budget needs. `observe` keeps only the calls
    # made inside a phase deadline — see `phase_budget.observed` for why that
    # one condition is what makes the sample the right one.
    observe(agent_name, elapsed)

    status = "ok" if error is None else "error"
    record: dict[str, Any] = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "engagement_id": current_engagement_id(),
        "call_id": call_id, "agent": agent_name, "model": model, "messages": messages,
        "latency_ms": round(elapsed * 1000, 1), "status": status,
        "attempts": len(retried or []) + 1,
        # What the call asked for and what LiteLLM put on the wire — see
        # `model_registry.decoding` for why the two are recorded separately.
        "decoding": {"requested": decoding_kwargs(model), "sent": sent_decoding(model)},
    }
    if retried:
        record["retried_after"] = list(retried)
    served = served_model_so_far()
    if served:
        # One call moved to its fallback after its own retries were spent.
        record["served_model"] = served
    if response is not None:
        _response_fields(record, response)
    if error is not None:
        record["error"] = repr(error)

    _write_jsonl(record)
    _emit_metrics(agent_name, model, status, elapsed, record, response)
