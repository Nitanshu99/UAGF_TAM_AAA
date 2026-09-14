"""Keep every run's deliverables, not just the last one.

``save_customer_artefacts`` writes six files under
``data/customer/<company>/`` and each run overwrites the previous one. That was
fine while a re-run meant "the same audit, done again". It stopped being fine
the moment runs started differing in ways worth comparing: on 2026-09-09/10 the
same engagement was run against a mock CGSA and a real S5 export, under two
providers and two models, and each result was destroyed by the next.

So the six files stay where they are — ``aaa report``, the wizard and every
existing consumer still find the latest — and a copy of each run is kept beside
them under ``runs/<timestamp>__<run_id>/`` with a manifest naming what produced
it. Immutable by convention: nothing here ever rewrites an existing folder.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aaa.data.writer.manifest import _ARCHIVED, _manifest

logger = logging.getLogger(__name__)







def archive_run(cdir: Path, engagement_id: str, state: dict[str, Any]) -> Path | None:
    """Copy this run's deliverables into an immutable per-run folder.

    Best-effort, like the export it follows: a failure here costs the archive,
    never the delivery.

    :param cdir: The company directory the deliverables were just written to.
    :param engagement_id: Engagement identifier.
    :param state: Final ``AuditState``, already carrying ``run_integrity``.
    :returns: The run folder, or ``None`` when nothing could be archived.
    """
    try:
        integrity = state.get("run_integrity") or {}
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = cdir / "runs" / f"{stamp}__{str(integrity.get('run_id') or 'norunid')[:8]}"
        if run_dir.exists():
            logger.warning("Archive: %s already exists; leaving it untouched.", run_dir)
            return run_dir
        run_dir.mkdir(parents=True)
        copied = 0
        for suffix in _ARCHIVED:
            source = cdir / f"{engagement_id}{suffix}"
            if source.is_file():
                shutil.copy2(source, run_dir / source.name)
                copied += 1
        (run_dir / "run.json").write_text(
            json.dumps(_manifest(state, engagement_id), indent=2, default=str),
            encoding="utf-8")
        logger.info("Archived %d deliverable(s) for %s → %s",
                    copied, engagement_id, run_dir)
        return run_dir
    except Exception as exc:  # noqa: BLE001 — the archive must never break a run
        logger.warning("Archive failed for %s: %s", engagement_id, exc)
        return None


__all__ = ["archive_run"]
