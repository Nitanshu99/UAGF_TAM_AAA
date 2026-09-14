"""Part 2 of the former ``cli`` module (auto-split)."""
from __future__ import annotations

import argparse
import pathlib
from typing import TYPE_CHECKING

from aaa.cli.logger import _load_json, _summarise, logger  # noqa: F401
from aaa.cli.seed.documents import seed_client_documents

if TYPE_CHECKING:
    from aaa.agents.base import IntakeDispatch
    from aaa.platform.evidence import EvidenceStore


def _seed_intake(store: "EvidenceStore", intake_dir: pathlib.Path,
                 args: argparse.Namespace) -> "IntakeDispatch":
    """Seed the Stage A/B/C raw payloads and build the intake dispatch.

    :param store: Evidence store receiving the raw payloads.
    :param intake_dir: Directory with ``stage_a.json`` / ``stage_b.json``
        (and optionally ``stage_c.json``).
    :param args: Parsed CLI arguments.
    :returns: The dispatch handed to the IntakeValidator.
    """
    stage_a = _load_json(intake_dir / "stage_a.json")
    stage_b = _load_json(intake_dir / "stage_b.json")
    stage_c_path = intake_dir / "stage_c.json"
    stage_c = _load_json(stage_c_path) if stage_c_path.exists() else None

    # Stage the declared documents before Stage B is written, so the payload the
    # IntakeValidator reads names stored artefacts rather than filesystem paths
    # the ingest cannot open. Without this the CLI audits with an empty
    # client-document collection and says so only in a warning.
    seed_client_documents(store, args.engagement_id, stage_b, intake_dir)

    stage_a_uri = store.store_artefact(
        args.engagement_id, "stage_a_raw", "stage_a_raw", stage_a, "cli")
    stage_b_uri = store.store_artefact(
        args.engagement_id, "stage_b_raw", "stage_b_raw", stage_b, "cli")
    stage_c_uri = (
        store.store_artefact(
            args.engagement_id, "stage_c_raw", "stage_c_raw", stage_c, "cli")
        if stage_c is not None else None
    )
    return {
        "engagement_id": args.engagement_id,
        "stage_a_uri": stage_a_uri,
        "stage_b_uri": stage_b_uri,
        "stage_c_uri": stage_c_uri,
        "annex_iv_schema_version": args.annex_iv_schema_version,
    }
