"""Propagates the current engagement id to LLM calls and to the audit trail.

Bound once per engagement in :func:`aaa.agents.tier1.orchestrator.runner.run`,
which every entry point funnels through, so the Orchestrator's own ReAct turns
and the Verifier's critiques are attributable and not only the phase agents'
calls (finding F7). :func:`aaa.agents.tier1.phases.agent_runner._invoke` binds
again per dispatch; the inner binding is a narrowing, never a clearing.

Read by :meth:`aaa.agents.base.agent.BaseAgent.acompletion`, which tags the
completion with ``metadata={"session_id": ...}`` so one engagement's LLM calls
land in a single Langfuse session, and by
:func:`aaa.agents.base.audit.write_audit`, which stamps the id onto every
record in the append-only trail. Calls outside any engagement (document
extraction from the wizard binds its own) simply get no id — tracing still
records them.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_engagement_id: ContextVar[str | None] = ContextVar("engagement_id", default=None)


@contextmanager
def bind_engagement_id(engagement_id: str | None) -> Iterator[None]:
    """Bind *engagement_id* for the duration of the ``with`` block.

    An empty or ``None`` id binds *nothing* and leaves any outer binding in
    place, which is what the parameter has always promised. Setting it would
    make the inner ``with`` a clearing rather than a narrowing: a phase
    dispatch that declares no engagement id would strip the id bound around
    the whole engagement, and its agent's calls would land in the trail
    unattributed — the F7 symptom, re-introduced one layer down.

    :param engagement_id: Engagement identifier, or ``None`` to bind nothing.
    :type engagement_id: str | None
    """
    if not engagement_id:
        yield
        return
    token = _engagement_id.set(engagement_id)
    try:
        yield
    finally:
        _engagement_id.reset(token)


def current_engagement_id() -> str | None:
    """Return the engagement id bound by the innermost :func:`bind_engagement_id`.

    :returns: The bound engagement id, or ``None`` outside any binding.
    :rtype: str | None
    """
    return _engagement_id.get()


def with_session_metadata(call_kwargs: dict, agent_name: str) -> dict:
    """Inject Langfuse session/tag metadata into LiteLLM call kwargs.

    :param call_kwargs: The LiteLLM call kwargs, unmodified if no engagement
        is bound.
    :type call_kwargs: dict
    :param agent_name: Name tagged onto the trace (the calling agent).
    :type agent_name: str
    :returns: *call_kwargs* with ``metadata`` populated; caller-supplied
        metadata keys always win over the injected defaults.
    :rtype: dict
    """
    engagement_id = current_engagement_id()
    if not engagement_id:
        return call_kwargs
    call_kwargs["metadata"] = (
        {"session_id": engagement_id, "tags": [agent_name]}
        | call_kwargs.get("metadata", {}))
    return call_kwargs
