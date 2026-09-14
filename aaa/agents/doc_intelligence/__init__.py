"""DocIntelligenceAgent — pre-intake document extraction (§6 Stage 0 extension).

Reads all customer-uploaded artefacts from an engagement's EvidenceStore
(already ingested into the per-engagement Qdrant collection) and extracts
every Stage A / Stage B field it can find, returning a
:class:`~aaa.platform.state.DocExtractionResult` that the wizard UI uses to
pre-populate the review form.

Model: gpt-5.6-terra on the **default (non-Flex) tier** — this agent is on the
interactive critical path (the user waits for it) and must not risk a 429
from spare-capacity exhaustion that Flex processing can surface at peak load.

When no documents are provided the agent returns an empty result immediately
(no Qdrant / OpenAI credentials needed) so the wizard still works without
infrastructure.
"""
from __future__ import annotations

from aaa.agents.doc_intelligence.agent import DocIntelligenceAgent

__all__ = ["DocIntelligenceAgent"]
