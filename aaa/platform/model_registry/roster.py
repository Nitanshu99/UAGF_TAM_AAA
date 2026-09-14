"""The default (OpenAI) agent roster and the set of agents allowed on the Flex tier.

Provider mirrors live beside it: :mod:`nvidia_roster` and :mod:`openrouter.roster`.
Which one is active is decided per call in :mod:`aaa.platform.model_registry.resolve`.
"""
from __future__ import annotations

from aaa.platform.model_registry.model_config import ModelConfig

# GPT-5.6 migration (2026-08): only gpt-5.6-luna supports the Flex tier —
# Sol/Terra reject the ``service_tier`` param — so no agent ships a tier now.
# The Luna agents stay on the standard tier: latency compounds over their
# many short calls. ``AAA_DISABLE_FLEX`` remains as the global kill-switch.
FLEX_AGENTS: frozenset[str] = frozenset()


AGENT_MODELS: dict[str, ModelConfig] = {
    # 1. Orchestrator — high-reasoning planner, short prompts, on critical path.
    "Orchestrator":         ModelConfig("gpt-5.6-sol"),
    # 2. Verifier — critical critique over all artefacts; ~68% of pipeline
    # tokens, so Terra (not Sol) keeps the audit affordable.
    "Verifier":             ModelConfig("gpt-5.6-terra"),
    # 3. Regulatory RAG — top-K chunk QA, short prompts.
    "Regulatory RAG":       ModelConfig("gpt-5.6-luna"),
    # 4. Phase 1 — Annex III classification.
    "ScopeAgent":           ModelConfig("gpt-5.6-terra"),
    # 5. Phase 2 — Dataset lineage / governance, long context.
    "DataAuditor":          ModelConfig("gpt-5.6-terra"),
    # 6. Phase 3 — Model validation + evals.
    "ModelValidator":       ModelConfig("gpt-5.6-terra"),
    # 7. Phase 4 — Bounded fairness interpretation, short prompts.
    "OutputFairnessTester": ModelConfig("gpt-5.6-luna"),
    # 8. Phase 5 — CGSA ingest + Art. 9 chain.
    "GovernanceAgent":      ModelConfig("gpt-5.6-terra"),
    # 9. Phase 6 — Assembles all artefacts.
    "ReportArchitect":      ModelConfig("gpt-5.6-terra"),
    # 10. UAGF-TAM-L — RAGAs + trajectory audit.
    "UAGF-TAM-L":           ModelConfig("gpt-5.6-terra"),
    # 11. Cybersecurity — targeted Art. 15 evidence.
    "CyberSecurityAgent":   ModelConfig("gpt-5.6-terra"),
    # 12. Privacy / DPO — GDPR overlap check.
    "PrivacyDPOAgent":      ModelConfig("gpt-5.6-terra"),
    # 13. DocIntelligenceAgent — pre-intake field extraction from customer uploads.
    # On the interactive critical path; user waits for this.
    "DocIntelligenceAgent": ModelConfig("gpt-5.6-terra"),
    # 14. ClientBrief — rewrites the finished audit for the customer. Long
    # context (one article's evidence per call) and the reasoning to hold a
    # declaration against an observation, so it sits with the Terra agents.
    "ClientBrief":          ModelConfig("gpt-5.6-terra"),
}


__all__ = ["AGENT_MODELS", "FLEX_AGENTS"]
