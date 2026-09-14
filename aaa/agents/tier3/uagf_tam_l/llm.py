"""LLM synthesis for UAGF-TAM-L (Agent 10 prompt over the eval-suite output).

Golden-set scoring, RAGAs metrics and the injection suite stay deterministic
tools; the model writes the T16 narrative and verdict rationale. The
deterministic verdict remains authoritative — the narrative never changes it.

The L branch did not run on case 01, so Q4 never caught it here — but it was the
third copy of the same call, with the same hole in it. It goes through the same
closed-retrieval path as the other two spawns (fix 28) rather than waiting for
cases 04/05 to demonstrate the defect again.
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.narrative import run_narrative_synthesis, with_narrative  # noqa: F401

_PROMPT_NAME = "uagf_tam_l"

#: What the L-branch looks for in the client's own dossier (T-20260913-029). The
#: evidence an LLM audit rests on is the system prompt, the RAG manifest and the
#: guardrail configuration — all uploaded, and never searched before this.
_DOC_QUERY = ("system prompt, RAG manifest and retrieval sources, guardrail configuration, "
              "prompt-injection and jailbreak controls, hallucination and groundedness "
              "testing, golden-set evaluation, human oversight of generated output, "
              "transparency to users")

#: Reply keys the Agent 10 prompt may return its narrative under.
_NARRATIVE_KEYS = ("evaluation_narrative", "summary")


async def run_llm_synthesis(agent: Any, decl: dict[str, Any],
                            t16: dict[str, Any]) -> tuple[str | None, str]:
    """Interpret the T16 evidence with the Agent 10 prompt.

    :param agent: The :class:`UagfTamLBranch` instance.
    :param decl: Dispatch declaration summary.
    :param t16: The assembled T16 evidence artefact.
    :returns: ``(narrative or None, prompt_note)``.
    """
    return await run_narrative_synthesis(
        agent, _PROMPT_NAME,
        # `declared_controls` is what the client's own guardrail configuration
        # and RAG manifest state. Without it the narrative reasoned about the
        # injection suite's results with no idea that the configuration beside
        # them declares injection detection as not yet implemented — the answer
        # was in a document the audit was holding and had never opened.
        {"declaration_summary": decl,
         "golden_set_results": t16.get("golden_set_results"),
         "prompt_injection_results": t16.get("prompt_injection_results"),
         "declared_controls": t16.get("declared_controls"),
         "trajectory_audit": t16.get("trajectory_audit"),
         "overall_verdict": t16.get("overall_verdict")},
        keys=_NARRATIVE_KEYS,
        engagement_id=str(decl.get("engagement_id") or ""),
        client_doc_query=_DOC_QUERY)
