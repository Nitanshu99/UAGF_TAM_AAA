"""The single batched field-extraction LLM call."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.doc_intelligence.prompt import PROMPT_NAME
from aaa.agents.doc_intelligence.queries import FIELD_QUERIES

logger = logging.getLogger(__name__)


async def extract_fields(agent: Any,
                         field_contexts: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Run one batched LLM call extracting every field with a context.

    :param agent: The calling :class:`DocIntelligenceAgent` instance.
    :param field_contexts: Field → retrieval context from the search step.
    :returns: Field → ``{value, confidence}`` mapping, or ``None`` when the
        call fails.
    """
    user_payload = {
        "task": ("Extract EU AI Act compliance form fields from retrieved "
                 "document contexts."),
        "fields": {field: {"description": FIELD_QUERIES[field],
                           "context": data["context"]}
                   for field, data in field_contexts.items()},
    }
    try:
        return await agent.acompletion_json(PROMPT_NAME, user_payload)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("[DocIntelligenceAgent] LLM call failed: %s", exc)
        return None
