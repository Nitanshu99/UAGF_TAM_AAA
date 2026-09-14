"""The one mock LLM call, made through the production seam."""
from __future__ import annotations

from typing import Any

#: A real provider slug so LiteLLM resolves pricing/usage like a live call.
PROBE_MODEL = "openai/gpt-4o-mini"
AGENT_NAME = "ObsProbe"


async def probe_call(probe_id: str) -> dict[str, Any]:
    """Make the mock call as an agent would and return what was recorded.

    :param probe_id: Unique marker written into the prompt, the reply, the
        Langfuse trace name and the engagement id.
    :returns: agent, model, engagement_id and the reply text.
    """
    from aaa.agents.base.agent import BaseAgent
    from aaa.observability.logging_config import configure_logging
    from aaa.observability.trace_context import bind_engagement_id
    from aaa.observability.tracing import flush_llm_tracing

    configure_logging()

    class _Probe(BaseAgent):
        async def process(self, message: Any) -> Any:
            return message

    agent = _Probe(name=AGENT_NAME, model=PROBE_MODEL)
    engagement_id = f"eng-{probe_id}"
    messages = [{"role": "system", "content": "AAA observability probe — no provider call."},
                {"role": "user", "content": probe_id}]
    with bind_engagement_id(engagement_id):
        response = await agent.acompletion(
            messages=messages, mock_response=f"pong {probe_id}",
            metadata={"trace_name": probe_id, "tags": ["obs-probe"]})
    # Same seam the Orchestrator runner awaits: drains LiteLLM's callback
    # queue and exports the OTEL batch before this process exits.
    await flush_llm_tracing()
    return {"agent": AGENT_NAME, "model": PROBE_MODEL, "engagement_id": engagement_id,
            "content": response.choices[0].message.content}
