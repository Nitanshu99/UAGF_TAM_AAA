"""Critique prompt construction for the Verifier LLM path.

The static rubric, reasoning procedure, security policy and output contract
live in ``_SYSTEM_PROMPT`` so that the prefix is byte-identical across every
Verifier call.  This (a) lets the model server reuse cached key/value state
(OpenAI auto-prefix-cache ≥ 1024 tokens, Anthropic ``cache_control``) and
(b) keeps untrusted artefact content out of the instruction surface, where
it could otherwise be mistaken for a directive.

Per-call variability (phase, template, evidence list, artefact body) is
placed in the *user* message inside XML tags that the system prompt
explicitly designates as DATA, not instructions.
"""
from __future__ import annotations

import json
from typing import Any

from aaa.platform.prompt_registry import load_prompt

_SYSTEM_PROMPT = load_prompt("verifier")


def _build_critique_messages(
    phase_id: str,
    template_id: str,
    content_str: str,
    evidence_uris: list[str],
    artefact_uri: str = "",
    declaration_summary: dict[str, Any] | None = None,
    regulatory_hits: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Return a ``[system, user]`` message pair for ``litellm.acompletion``.

    ``regulatory_hits`` carries the corpus text for the articles the artefact
    cites.  It is DATA like the rest of the user message: the citation rule in
    the system prompt reads it, and an empty list means retrieval was
    unavailable — never that the article does not exist.
    """
    try:
        artefact_payload: Any = json.loads(content_str)
    except Exception:
        artefact_payload = content_str
    user_content = json.dumps(
        {
            "review_request": {
                "phase_id": phase_id,
                "template_id": template_id,
                "artefact_uri": artefact_uri,
                "artefact_payload": artefact_payload,
                "declaration_summary": declaration_summary or {},
                "prior_critique": None,
                "evidence_uris": evidence_uris,
                "regulatory_hits": regulatory_hits or [],
            }
        },
        indent=2,
        default=str,
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
