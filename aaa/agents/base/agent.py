"""The BaseAgent ABC — LLM access with retry, auditing, and prompt registry."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from aaa.agents.base import prompts
from aaa.agents.base.call import audited_acompletion
from aaa.agents.base.json_utils import _loads_lenient


class BaseAgent(ABC):
    """Common LLM plumbing shared by every pipeline agent.

    :param name: Agent display name (used in audit records).
    :param model: LiteLLM model string.
    :param service_tier: Optional OpenAI service tier (e.g. ``"flex"``).
    :param timeout: Optional per-agent LLM ceiling in seconds. ``None`` takes
        the platform default; see
        :mod:`aaa.platform.model_registry.timeouts` for why the Verifier does
        not (P6, P8).
    """

    def __init__(self, name: str, model: str, service_tier: Optional[str] = None,
                 timeout: Optional[float] = None):
        self.name = name
        self.model = model
        self.service_tier = service_tier
        self.timeout = timeout

    def _litellm_kwargs(self) -> dict:
        """Return ``model`` (and ``service_tier`` / ``timeout`` if set) as kwargs."""
        kw: dict = {"model": self.model}
        if self.service_tier is not None:
            kw["service_tier"] = self.service_tier
        if self.timeout is not None:
            kw["timeout"] = self.timeout
        return kw

    async def acompletion(self, **kwargs) -> Any:
        """Async LiteLLM call with transient/Flex retry and full audit logging.

        Merges ``self._litellm_kwargs()`` with any extra *kwargs*, delegates
        to :func:`aaa.platform.flex_retry.flex_acompletion`, and records the
        full request/response/cost to the LLM audit trail — including whether
        the reply took one attempt or was recovered from a transient provider
        failure (fix 39).
        """
        from aaa.observability.trace_context import with_session_metadata

        call_kwargs = with_session_metadata({**self._litellm_kwargs(), **kwargs}, self.name)
        return await audited_acompletion(self.name, call_kwargs, self.model)

    async def acompletion_json(self, prompt_name: str, user_payload: Any,
                               **kwargs) -> dict[str, Any]:
        """Run a prompt-registry-backed completion and parse a JSON response.

        :param prompt_name: PROMPT.md section name for this agent.
        :param user_payload: JSON-serialisable user payload.
        :returns: The parsed JSON object from the model reply.
        """
        from aaa.platform.prompt_registry import load_prompt

        messages = [
            {"role": "system", "content": load_prompt(prompt_name)},
            {"role": "user", "content": json.dumps(user_payload, indent=2, default=str)},
        ]
        response_format = kwargs.pop("response_format", {"type": "json_object"})
        response = await self.acompletion(
            messages=messages, response_format=response_format, **kwargs)
        content = getattr(response.choices[0].message, "content", None) or "{}"
        return _loads_lenient(content)

    prompt_metadata = prompts.prompt_metadata
    prompt_note = prompts.prompt_note

    @abstractmethod
    async def process(self, message: Any) -> Any:
        """Handle one dispatch message; implemented by each agent."""
