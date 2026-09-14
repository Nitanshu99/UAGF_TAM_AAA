"""The ClientBriefAgent — the audit's result, written for the people audited.

The T18 report and its PDF are addressed to a conformity assessor: they cite
template ids and artefact URIs, and they state verdicts without explaining what
produced them. The customer who commissioned the audit reads neither. This
agent writes the same result again, article by article, as the contrast that
actually decided it — what the submission claimed, what the evidence showed,
and which obligation the gap between them falls under.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.agents.tier2.client_brief.compose import (  # noqa: F401  (test imports it here)
    FAILURES_BEFORE_GIVING_UP,
    build_brief,
)
from aaa.agents.tier2.client_brief.constants import TEMPLATE_ID
from aaa.platform.evidence import EvidenceStore

logger = logging.getLogger(__name__)

#: Consecutive failed sections after which the remaining ones are assembled
#: without calling the model.
#:
#: One failure is a bad minute — fix 39's retry and the 504 reclassification both
#: exist to absorb that, and abandoning the narrative on it would throw away a
#: brief the provider was willing to write. Three in a row is not a minute.
#:
#: Unbounded, the cost is paid per article: with the 420 s ceiling this agent
#: carries, a dead provider took **17 × 420 s ≈ 2 hours** to produce a brief that
#: was deterministic from its first section. It also made every pipeline test 17


class ClientBriefAgent(BaseAgent):
    """Phase 6b — composes the plain-language client brief from the final state."""

    def __init__(self, evidence_store: EvidenceStore, regulatory_rag: Any = None,
                 model: str | None = None, service_tier: str | None = None,
                 timeout: float | None = None):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        from aaa.platform.model_registry.timeouts import resolve_timeout
        super().__init__(
            name="ClientBrief",
            model=resolve_model("ClientBrief", model),
            service_tier=resolve_service_tier("ClientBrief", service_tier),
            # Only binds on the `aaa brief` path, which binds no phase deadline
            # and otherwise takes a 120 s default this agent's sections outrun.
            timeout=resolve_timeout("ClientBrief", timeout),
        )
        self.store = evidence_store
        self.rag = regulatory_rag

    async def build_brief(self, state: dict[str, Any], engagement_id: str) -> str:
        """Write the brief for *state* and return it as Markdown.

        :param state: Final ``AuditState``, after the compliance matrix is set.
        :param engagement_id: Engagement identifier.
        :returns: The complete Markdown brief.
        """
        return await build_brief(self, state, engagement_id)

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """Write the brief and store it, returning its artefact URI.

        :param message: Dispatch whose ``declaration_summary`` is the full
            final ``AuditState``.
        :returns: Report carrying the stored brief's URI.
        """
        state = message.get("declaration_summary", {})
        engagement_id: str = state.get("engagement_id") or message["phase_id"]
        markdown = await self.build_brief(state, engagement_id)
        content = {"format": "markdown", "body": markdown,
                   "bytes_size": len(markdown.encode("utf-8"))}
        uri = self.store.store_artefact(
            engagement_id=engagement_id, phase="phase_6",
            artefact_type=TEMPLATE_ID, content=content, agent_name=self.name)
        ref = {"uri": uri, "template_id": TEMPLATE_ID,
               "sha256": hashlib.sha256(json.dumps(content).encode()).hexdigest()}
        return Report(
            phase_id=message["phase_id"], artefact_uri=uri,
            summary=f"Client brief written for {engagement_id} "
                    f"({len(markdown):,} characters).",
            confidence=1.0, tool_calls=[],
            declaration_verification_delta={"phase_artefacts": {TEMPLATE_ID: ref}})
