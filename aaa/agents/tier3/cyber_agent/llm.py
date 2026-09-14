"""LLM synthesis for the CyberSecurityAgent (Agent 11 prompt over probe output).

The probes stay deterministic tools; the model interprets their results —
severity reasoning and an Art. 15 narrative — merged into the T11 extension.
Any failure keeps the deterministic artefact and labels the fallback.

Since fix 28 the call goes through
:func:`~aaa.agents.tier3.narrative.run_narrative_synthesis`, which closes
retrieval explicitly and refuses a plan in the answer position (Q4).
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.narrative import run_narrative_synthesis, with_narrative  # noqa: F401

_PROMPT_NAME = "cyber"

#: Reply keys the Agent 11 prompt may return its narrative under.
_NARRATIVE_KEYS = ("security_narrative", "summary")

#: The dossier question this spawn asks. Art. 15 robustness and cybersecurity
#: are documented in the provider's own security policy and guardrail
#: configuration, not in the probe output the spawn already holds (M13).
_DOC_QUERY = ("security policy, access control, threat model, penetration test, "
              "incident response, guardrails and input filtering, model and "
              "prompt-injection hardening, accuracy and robustness measures")


async def run_llm_synthesis(agent: Any, decl: dict[str, Any],
                            probes: list[dict[str, Any]],
                            injection: dict[str, Any] | None,
                            blocking: list[Any]) -> tuple[str | None, str]:
    """Interpret probe results with the Agent 11 prompt.

    :param agent: The :class:`CyberSecurityAgent` instance.
    :param decl: Dispatch declaration summary.
    :param probes: Combined probe entries feeding the T11 extension.
    :param injection: Injection-suite results, when run.
    :param blocking: Blocking findings raised by the probes.
    :returns: ``(narrative or None, prompt_note)``.
    """
    return await run_narrative_synthesis(
        agent, _PROMPT_NAME,
        {"declaration_summary": decl, "probes": probes[:12],
         "injection_results": injection, "blocking_findings": blocking},
        keys=_NARRATIVE_KEYS,
        engagement_id=str(decl.get("engagement_id") or ""),
        client_doc_query=_DOC_QUERY)
