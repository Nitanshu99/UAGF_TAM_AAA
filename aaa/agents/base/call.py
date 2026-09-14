"""One audited LLM call: session metadata, transient/Flex retry, and the audit record."""
from __future__ import annotations

import time
import uuid
from typing import Any

from aaa.agents.base.audit import write_audit


async def audited_acompletion(agent_name: str, call_kwargs: dict[str, Any],
                              default_model: str) -> Any:
    """Make one LiteLLM call through the Flex/transient retry and audit it.

    Delegates to :func:`aaa.platform.flex_retry.flex_acompletion` and records
    the full request/response/cost to the LLM audit trail — including whether
    the reply took one attempt or was recovered from a transient provider
    failure (fix 39). A failure is audited and then re-raised.

    :param agent_name: The calling agent's display name (audit ``agent_name``).
    :param call_kwargs: The complete LiteLLM keyword arguments.
    :param default_model: The agent's model, used when *call_kwargs* names none.
    :returns: The LiteLLM response.
    """
    from aaa.platform.flex_retry import flex_acompletion
    from aaa.platform.transient_retry import record_attempts

    model = call_kwargs.get("model", default_model)
    messages = call_kwargs.get("messages", [])
    call_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    with record_attempts() as retried:
        try:
            response = await flex_acompletion(**call_kwargs)
        except Exception as exc:
            write_audit(agent_name, model, messages, call_id, t0,
                        error=exc, retried=retried)
            raise
        write_audit(agent_name, model, messages, call_id, t0,
                    response=response, retried=retried)
    return response


__all__ = ["audited_acompletion"]
