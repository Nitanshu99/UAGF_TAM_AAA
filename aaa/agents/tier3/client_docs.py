"""The client-upload evidence a tier-3 spawn searches before it writes its narrative."""
from __future__ import annotations

import logging
from typing import Any

from aaa.tools.evidence_retrieval import seed_client_doc_hits
from aaa.tools.evidence_retrieval.terminal_round import TERMINAL_NOTICE

logger = logging.getLogger(__name__)


#: The same block for a spawn that *was* given the engagement's dossier. Saying
#: "no client-document search will run" to a model holding ``client_doc_hits``
#: would be the inverse of the honesty this notice exists for.
SPAWN_CLIENT_DOCS_SEARCHED: dict[str, Any] = {
    "round": 0, "final_round": True, "retrieval_closed": True,
    "regulatory_queries": [], "client_doc_queries": [],
    "notice": ("The engagement's client-document dossier has been searched for "
               "you and every hit is in `client_doc_hits`; no further search, "
               "and no regulatory search at any point, will run for this "
               "sub-agent. " + TERMINAL_NOTICE),
}
def _client_docs(agent: Any, engagement_id: str, query: str) -> list[dict[str, Any]]:
    """Search the engagement dossier for a spawn, degrading to no hits.

    Retrieval must not cost the narrative: the spawn's numbers are already
    measured and its reasoning is what the call exists for, so a dossier that
    cannot be reached is fewer hits, never a lost report.

    :param agent: The spawn, for the log line only.
    :param engagement_id: Engagement whose dossier to search; ``""`` disables.
    :param query: The spawn's client-document question; ``""`` disables.
    :returns: Score-ranked hits, or ``[]``.
    """
    if not engagement_id or not query:
        return []
    try:
        return seed_client_doc_hits(engagement_id, query)
    except Exception as exc:  # noqa: BLE001 - retrieval must not cost a narrative
        logger.warning("%s: client-document search failed (%s); continuing with none.",
                       getattr(agent, "name", "tier-3 spawn"), exc)
        return []


__all__ = ["SPAWN_CLIENT_DOCS_SEARCHED", "_client_docs"]
