"""AI pre-fill endpoint backed by the DocIntelligenceAgent."""
from __future__ import annotations

from typing import Any

from aaa.api.routes.workflow.base import require_engagement, router
from aaa.api.store import get_store


@router.post("/{engagement_id}/extract-triage", summary="AI pre-fill from uploaded docs")
async def extract_triage(engagement_id: str) -> dict[str, Any]:
    """Run DocIntelligenceAgent over uploaded files and return pre-filled fields.

    :param engagement_id: Engagement whose uploads are analysed.
    :returns: :class:`~aaa.platform.state.DocExtractionResult` as a dict.
    """
    require_engagement(engagement_id)
    from aaa.agents.doc_intelligence import DocIntelligenceAgent
    store = get_store(engagement_id)
    doc_uris = [
        uri
        for uri, meta in store._store.items()  # type: ignore[attr-defined]
        if isinstance(meta, dict) and meta.get("engagement_id") == engagement_id
        and meta.get("phase") == "customer_uploads"
    ]
    agent = DocIntelligenceAgent(evidence_store=store)
    result = await agent.process({"engagement_id": engagement_id, "doc_uris": doc_uris})
    return dict(result)
