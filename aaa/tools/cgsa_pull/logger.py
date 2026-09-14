"""Part 1 of the former ``cgsa_pull`` module (auto-split)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from aaa.tools.cgsa_ingest.s5.dialect import is_s5_dialect
from aaa.tools.cgsa_pull.fixture_roots import _find_fixture, fixture_roots

logger = logging.getLogger(__name__)


_PINNED_SCHEMA_VERSION = os.environ.get("CGSA_SCHEMA_VERSION", "1.0.0")


_DEFAULT_BASE_URL = os.environ.get("S4_CGSA_BASE_URL", "http://localhost:8001")









_MAX_ATTEMPTS = 5


_BACKOFF_BASE_SECONDS = 1.0


class CGSAPullError(Exception):
    """Raised when the CGSA payload cannot be retrieved or version-pinned."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[cgsa_pull] {reason}")


def _read_fixture(
    assessment_id: str,
    fixture_dir: str | None,
    pinned_version: str,
) -> dict[str, Any]:
    """Read a CGSA fixture from disk; supports both <id>.json and direct paths."""
    roots = fixture_roots(fixture_dir)
    if not roots:
        raise CGSAPullError(
            "fixture_dir_not_set",
            {"hint": "Set CGSA_FIXTURE_DIR or pass fixture_dir=...",
             "configured": fixture_dir},
        )
    candidate = _find_fixture(assessment_id, roots)
    if candidate is None:
        # Naming what was searched is the difference between "the fixture is
        # missing" and "you pointed me at the wrong case's directory" — the
        # 2026-09-11 UI run failed the second way and reported the first.
        raise CGSAPullError(
            "fixture_not_found",
            {"assessment_id": assessment_id, "searched": roots},
        )
    with open(candidate, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    declared = payload.get("schema_version") or payload.get("metadata", {}).get(
        "schema_version"
    )
    # A dialect this repo can translate is not drift. S5 ships its hand-off as
    # `s5-aaa-adapter-v1.0`, which `cgsa_ingest` restates in the pinned contract
    # (see `cgsa_ingest.s5.dialect`); rejecting it here would fail the pull
    # before the translation that exists for it could run.
    if is_s5_dialect(payload):
        logger.info("cgsa_pull: fixture declares the S5 dialect (%s); it will be "
                    "translated to the pinned contract at ingest.", declared)
    elif declared and declared != pinned_version:
        raise CGSAPullError(
            "schema_version_drift",
            {"pinned": pinned_version, "got": declared, "path": candidate},
        )
    logger.info("cgsa_pull: fixture loaded (%s)", candidate)
    return payload
