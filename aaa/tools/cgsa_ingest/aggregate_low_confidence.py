"""Part 4 of the former ``cgsa_ingest`` module (auto-split)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.logger import (  # noqa: F401
    _LOW_CONFIDENCE_THRESHOLD,
    _REQUIRED_TOP_LEVEL_KEYS,
    _VENDORED_SCHEMA,
    CGSAIngestError,
    IngestResult,
    logger,
)
from aaa.tools.cgsa_ingest.schema_validate import schema_validate  # noqa: F401
from aaa.tools.cgsa_ingest.shallow_required_check import _shallow_required_check  # noqa: F401


def _aggregate_low_confidence(handoff: dict[str, Any],
                              domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge CGSA-flagged and extracted low-confidence controls.

    :param handoff: The ``aaa_phase5_handoff`` block.
    :param domains: The CGSA domain list (controls carry ``confidence``).
    :returns: De-duplicated low-confidence control entries.
    """
    low_conf = list(handoff.get("low_confidence_controls", []) or [])
    seen_ids = {item.get("control_id") for item in low_conf}
    for dom in domains:
        for ctrl in dom.get("controls", []) or []:
            conf = ctrl.get("confidence")
            cid = ctrl.get("control_id")
            if conf is not None and conf < _LOW_CONFIDENCE_THRESHOLD and cid not in seen_ids:
                low_conf.append({
                    "control_id": cid,
                    "control_name": ctrl.get("control_name", ""),
                    "confidence": conf,
                    "flag_reason": (f"CGSA extraction confidence {conf:.2f} below "
                                    f"{_LOW_CONFIDENCE_THRESHOLD:.2f} threshold."),
                })
                seen_ids.add(cid)
    return low_conf
