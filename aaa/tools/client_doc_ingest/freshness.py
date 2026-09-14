"""Per-run reset of a client's document collection.

A returning customer is assumed to have updated their documents, so carrying
last run's vectors forward would search superseded text — the collection is
keyed on engagement, not on document content, so stale chunks would otherwise
survive indefinitely and outrank the new ones.

The reset is once per *run*, not once per call: ``client_doc_ingest`` is
invoked twice in a single pipeline (once by the DocIntelligence agent at upload
time, once by the IntakeValidator), and resetting on each call would delete the
first caller's chunks before the second had finished. Tracking which
engagements this process has already reset gives fresh vectors every run while
letting both callers contribute to the same collection.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Engagements already reset in this process.
_RESET_THIS_RUN: set[str] = set()


def reset_for_run(client: Any, collection: str, engagement_id: str) -> bool:
    """Drop *collection* the first time *engagement_id* is ingested this run.

    :param client: Qdrant client.
    :param collection: Per-engagement collection name.
    :param engagement_id: Engagement the documents belong to.
    :returns: Whether a reset was performed on this call.
    :rtype: bool
    """
    if engagement_id in _RESET_THIS_RUN:
        return False
    _RESET_THIS_RUN.add(engagement_id)
    try:
        if client.collection_exists(collection):
            client.delete_collection(collection_name=collection)
            logger.info(
                "Dropped stale client-document collection %s; documents are "
                "re-embedded on every run.", collection)
            return True
    except Exception:  # pylint: disable=broad-exception-caught
        # A reset failure must not abort intake: the worst case is that the
        # engagement keeps last run's vectors, which is the old behaviour.
        logger.warning("Could not reset collection %s; continuing.", collection)
    return False


def reset_tracking() -> None:
    """Forget which engagements were reset — test-only helper."""
    _RESET_THIS_RUN.clear()
