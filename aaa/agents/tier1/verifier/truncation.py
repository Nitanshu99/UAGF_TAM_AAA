"""Oversized-prompt recovery: compress evidence to fit the token budget."""
from __future__ import annotations

import json
from typing import Any

from aaa.agents.tier1.verifier.messages import _build_critique_messages
from aaa.platform.token_guard import compute_budget, count_tokens
from aaa.tools.evidence_truncate import truncate_payload


def truncate_for_budget(
    agent: Any,
    phase_id: str,
    template_id: str,
    content: Any,
    evidence_uris: list[str],
    artefact_uri: str = "",
    declaration_summary: dict[str, Any] | None = None,
    regulatory_hits: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Compress *content* with :func:`truncate_payload` and rebuild messages.

    :param agent: The Verifier instance (provides the model for budgeting).
    :returns: ``(content_str, messages)`` fitting within the prompt budget.
    """
    declaration_summary = declaration_summary or {}
    if not isinstance(content, dict):
        content_str = str(content)
        return content_str, _build_critique_messages(
            phase_id, template_id, content_str, evidence_uris,
            artefact_uri, declaration_summary, regulatory_hits,
        )
    budget = compute_budget(agent.model)
    # Estimate overhead from the system message + fixed user-message framing
    overhead_msgs = _build_critique_messages(
        phase_id, template_id, "", evidence_uris, artefact_uri, declaration_summary,
        regulatory_hits)
    overhead_tokens = count_tokens(agent.model, messages=overhead_msgs)
    payload_budget = max(1, budget - overhead_tokens)
    result = truncate_payload(
        content,
        query=f"{phase_id} {template_id}",
        model=agent.model,
        max_tokens=payload_budget,
        preserve_keys=("engagement_id", "generated_at"),
    )
    content_str = json.dumps(result.to_dict(), indent=2)
    messages = _build_critique_messages(
        phase_id, template_id, content_str, evidence_uris,
        artefact_uri, declaration_summary, regulatory_hits,
    )
    return content_str, messages
