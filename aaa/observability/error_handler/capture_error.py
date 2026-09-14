"""Part 2 of the former ``error_handler`` module (auto-split)."""
from __future__ import annotations

import json
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from aaa.observability.error_handler.logger import LOG_DIR, ErrorLogHandler, _logger  # noqa: F401


def capture_error(
    exc: BaseException,
    *,
    component: str = "app",
    context: dict[str, Any] | None = None,
    reraise: bool = True,
) -> None:
    """Log and persist an error record to ``logs/errors/<component>.jsonl``.

    Parameters
    ----------
    exc:
        The exception to record.
    component:
        Subsystem name — used as the JSONL filename stem.
        Suggested values: ``"api"``, ``"agents"``, ``"observability"``.
    context:
        Extra key/value pairs to include in the record (engagement_id, etc.).
    reraise:
        When *True* (default) re-raises *exc* after logging.
    """
    from aaa.observability.metrics import ERROR_COUNTER
    ERROR_COUNTER.labels(component=component, exception_type=type(exc).__name__).inc()

    error_id = str(uuid.uuid4())
    record: dict[str, Any] = {
        "error_id": error_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": traceback.format_exc(),
        **(context or {}),
    }

    _logger.error(
        "error_captured",
        error_id=error_id,
        component=component,
        exc_type=type(exc).__name__,
        **(context or {}),
    )

    out_path = LOG_DIR / "errors" / f"{component}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    except OSError:
        pass

    if reraise:
        raise exc
