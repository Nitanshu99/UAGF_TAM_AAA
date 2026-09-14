"""The Verifier class — independent critique gate for phase artefacts."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import BaseAgent
from aaa.agents.tier1.verifier.fallback import fallback_critique
from aaa.agents.tier1.verifier.llm import llm_critique
from aaa.agents.tier1.verifier.truncation import truncate_for_budget
from aaa.agents.tier1.verifier.verdicts import decide_verdict
from aaa.platform.model_registry import resolve_model, resolve_service_tier
from aaa.platform.model_registry.timeouts import resolve_timeout


class Verifier(BaseAgent):
    """Independent Verifier agent.

    :param model: LLM model string passed to LiteLLM.  Defaults to Claude
        Opus for maximum critique rigour.
    :param service_tier: Optional OpenAI service tier override.
    :param regulatory_rag: RegulatoryRAG used to resolve the articles an
        artefact cites.  Its own prompt has told it to *"resolve the article
        against Regulatory RAG output"* since fix 1, while the five phase
        agents held the only ``regulatory_rag`` instances — so the agent whose
        job is checking legal claims was the one that could not check them
        (F14).  ``None`` degrades to the pre-fix behaviour: citations are
        recorded unverified rather than denied.
    """

    #: bound implementations (kept as methods for compatibility)
    _fallback_critique = fallback_critique
    _llm_critique = llm_critique
    _truncate_for_budget = truncate_for_budget
    _decide_verdict = staticmethod(decide_verdict)

    def __init__(self, model: str | None = None, service_tier: str | None = None,
                 regulatory_rag: Any = None, timeout: float | None = None):
        super().__init__(
            name="Verifier",
            model=resolve_model("Verifier", model),
            service_tier=resolve_service_tier("Verifier", service_tier),
            timeout=resolve_timeout("Verifier", timeout),
        )
        self.rag = regulatory_rag

    async def process(self, message: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        """Critique a single phase artefact.

        :param message: Dict with ``phase_id``, ``template_id``, ``content``,
            ``evidence_uris``, ``rerun_count``, ``artefact_uri``, and
            ``declaration_summary``.
        :returns: A ``VerifierCritique`` dict: verdict, issues, notes,
            article citations, scores, and the rerun flag.
        """
        return await self._llm_critique(
            message.get("phase_id", ""),
            message.get("template_id", ""),
            message.get("content", {}),
            message.get("evidence_uris", []),
            int(message.get("rerun_count", 0)),
            message.get("artefact_uri", "") or "",
            message.get("declaration_summary", {}) or {},
        )
