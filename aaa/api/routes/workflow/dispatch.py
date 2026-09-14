"""Stage-payload persistence and IntakeDispatch construction for /run."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import IntakeDispatch
from aaa.platform.evidence import EvidenceStore


def build_dispatch(store: EvidenceStore, engagement_id: str,
                   payload: dict[str, Any]) -> IntakeDispatch:
    """Persist the raw stage payloads and build the intake dispatch.

    :param store: Evidence store for the engagement.
    :param engagement_id: Engagement identifier.
    :param payload: Submitted intake payload (stage_a / stage_b / stage_c).
    :returns: :class:`IntakeDispatch` referencing the stored stage URIs.
    """
    stage_a_uri = store.store_artefact(
        engagement_id, "stage_a_raw", "stage_a_raw", payload["stage_a"], "api")
    stage_b_uri = store.store_artefact(
        engagement_id, "stage_b_raw", "stage_b_raw", payload["stage_b"], "api")
    stage_c = payload.get("stage_c")
    stage_c_uri = (
        store.store_artefact(engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "api")
        if stage_c is not None else None
    )
    return {
        "engagement_id": engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": "1.0.0",
    }
