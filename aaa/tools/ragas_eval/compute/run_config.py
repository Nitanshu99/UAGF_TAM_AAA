"""ragas's run configuration for the audit's evaluations."""
from __future__ import annotations

from typing import Any

from aaa.tools.ragas_eval.logger import logger


def run_config() -> Any:
    """ragas's ``RunConfig``, with ``RAGAS_MAX_WORKERS`` setting its judge concurrency.

    Sixteen concurrent judge jobs (ragas's default, kept when unset) burst past a free
    route's per-minute limit (T-20260914-014).
    """
    import os

    from ragas.run_config import RunConfig

    raw = os.getenv("RAGAS_MAX_WORKERS", "").strip()
    if raw.isdigit() and int(raw) > 0:
        return RunConfig(max_workers=int(raw))
    if raw:
        logger.info("RAGAS_MAX_WORKERS=%r is not a positive integer; using ragas's default.", raw)
    return RunConfig()


__all__ = ["run_config"]
