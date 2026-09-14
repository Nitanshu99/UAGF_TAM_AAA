"""The deliverable lists every artefact that failed its template.

``suitable_for_handoff`` keeps its narrow meaning — no placeholders — so a
contract failure is reported beside it rather than folded into it.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.platform.evidence.contract import schema_violations

logger = logging.getLogger(__name__)


def stamp_schema_violations(integrity: dict[str, Any], final_state: dict[str, Any],
                            engagement_id: str, store: Any) -> None:
    """Add ``schema_invalid_artefacts`` to *integrity*, in place.

    ``None`` means the store could not be read, which is not the same as none failing.

    :param integrity: The run-integrity block being stamped.
    :param final_state: The finished AuditState.
    :param engagement_id: Engagement identifier.
    :param store: The evidence store the artefacts were written to.
    """
    try:
        index = store.get_index(engagement_id)
    except Exception as exc:  # noqa: BLE001 - an unreadable index must not block the write
        logger.error("Could not read the evidence index for %s (%s); schema violations "
                     "are unknown for this deliverable.", engagement_id, exc)
        integrity["schema_invalid_artefacts"] = None
        return
    invalid = schema_violations(index, final_state.get("phase_artefacts") or {})
    integrity["schema_invalid_artefacts"] = invalid
    if invalid:
        logger.error("Customer export: %s carries %d artefact(s) that violate their "
                     "template: %s. See each artefact's evidence-index entry for the errors.",
                     engagement_id, len(invalid), invalid)


__all__ = ["stamp_schema_violations"]
