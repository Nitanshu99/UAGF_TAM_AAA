"""LLM-backed four-dimension critique for the Verifier."""
from __future__ import annotations

import json
import logging
from typing import Any

from aaa.agents.tier1.verifier.citations import retrieve_cited_law
from aaa.agents.tier1.verifier.critique_call import _critique_once
from aaa.agents.tier1.verifier.fallback import fallback_critique
from aaa.agents.tier1.verifier.messages import _build_critique_messages
from aaa.agents.tier1.verifier.result import _result
from aaa.agents.tier1.verifier.truncation import truncate_for_budget
from aaa.platform.token_guard import BudgetExceededError, ensure_within_budget

logger = logging.getLogger(__name__)


async def llm_critique(
    agent: Any, phase_id: str, template_id: str, content: Any,
    evidence_uris: list[str], rerun_count: int, artefact_uri: str = "",
    declaration_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:  # pragma: no cover
    """Call the LLM for a structured four-dimension critique.

    Falls back to :func:`fallback_critique` on any failure.
    """
    declaration_summary = declaration_summary or {}
    try:
        content_str = (json.dumps(content, indent=2) if isinstance(content, dict)
                       else str(content))
        # F14: resolve the artefact's own citations before judging them. The
        # prompt has ordered this since fix 1; until now there was no channel.
        regulatory_hits = retrieve_cited_law(getattr(agent, "rag", None), content)
        messages = _build_critique_messages(
            phase_id, template_id, content_str, evidence_uris,
            artefact_uri, declaration_summary, regulatory_hits)
        try:
            ensure_within_budget(agent.model, messages=messages)
        except BudgetExceededError as exc:
            logger.warning(
                "Prompt for %s/%s exceeds budget (%d > %d); truncating evidence.",
                phase_id, template_id, exc.prompt_tokens, exc.budget)
            content_str, messages = truncate_for_budget(
                agent, phase_id, template_id, content, evidence_uris,
                artefact_uri, declaration_summary, regulatory_hits)
            ensure_within_budget(agent.model, messages=messages)
        raw = await _critique_once(agent, messages, phase_id, template_id)
    except Exception as exc:
        logger.warning("LLM critique failed (%s); applying deterministic fallback.", exc)
        return fallback_critique(
            agent, phase_id, template_id, content, evidence_uris, rerun_count,
            artefact_uri, reason=f"{type(exc).__name__}: {exc}"[:200])
    return _result(phase_id, template_id, raw, rerun_count, agent)
